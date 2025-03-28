import json
import logging
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from api.agent.llm import chat_completion
from api.agent.prompts import get_sequence_followup_prompt, get_system_prompt
from api.agent.tools import handle_tool
from api.models import Message, SessionLocal
from api.models import Session as SessionModel

# Import the emit_sequence_update function
from api.websocket import emit_sequence_update, socketio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, session_id: str, user_id: Optional[int] = None):
        self.session_id = session_id
        self.user_id = user_id if user_id else 1  # Default user ID
        self.messages = []
        self.load_messages()  # Load message history from database
        
    def load_messages(self):
        """Load message history from database"""
        try:
            db = SessionLocal()
            # Query for messages in this session, sorted by ID
            db_messages = db.query(Message).filter(
                Message.session_id == self.session_id
            ).order_by(Message.id).all()
            
            # Convert to format expected by OpenAI API
            for msg in db_messages:
                message_entry = {
                    "role": msg.role,
                    "content": msg.content
                }
                
                # Add tool calls if present
                if msg.tool_calls:
                    message_entry["tool_calls"] = msg.tool_calls
                
                self.messages.append(message_entry)
                
            logger.info(f"Loaded {len(self.messages)} messages from database")
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
        finally:
            db.close()
            
    def save_message(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None):
        """Save a message to the database"""
        try:
            db = SessionLocal()
            
            # Create message record
            message = Message(
                session_id=self.session_id,
                user_id=self.user_id,
                role=role,
                content=content,
                tool_calls=tool_calls
            )
            
            # Add to database
            db.add(message)
            db.commit()
            
            logger.info(f"Saved {role} message to database")
            
            # Add to local messages
            message_entry = {
                "role": role,
                "content": content
            }
            if tool_calls:
                message_entry["tool_calls"] = tool_calls
                
            self.messages.append(message_entry)
            
            # If this is the first assistant message, use it to name the session
            if role == 'assistant' and len(self.messages) <= 3:
                self._update_session_name(content, db)
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
        finally:
            db.close()
            
    def _update_session_name(self, content: str, db):
        """Update session name based on first assistant response"""
        try:
            # Get the session
            session = db.query(SessionModel).filter(
                SessionModel.id == self.session_id
            ).first()
            
            if not session:
                logger.warning(f"Session {self.session_id} not found in database")
                return
                
            # Check if session has default name (starts with "Session ")
            if session.name.startswith("Session "):
                # Generate a name from the first 30 chars of the response
                name_from_response = content[:30].strip()
                
                # Add ellipsis if truncated
                if len(content) > 30:
                    name_from_response += "..."
                    
                # Only update if it's a meaningful name
                if len(name_from_response) >= 5:
                    session.name = name_from_response
                    db.commit()
                    logger.info(f"Renamed session {self.session_id} to '{name_from_response}'")
        except Exception as e:
            logger.error(f"Error updating session name: {e}")
            
    async def process_message(self, content: str):
        """Process a user message and generate a response"""
        try:
            # Save user message to database
            self.save_message("user", content)
            
            # Prepare messages for API call
            messages_for_api = []
            
            # Add system prompt at the beginning
            system_prompt = get_system_prompt()
            messages_for_api.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Filter and clean messages before sending to API
            valid_messages = []
            has_tool_call = False
            
            # Only include valid messages
            for msg in self.messages:
                if msg["role"] == "tool":
                    # Only include tool messages if there was a preceding assistant message with tool_calls
                    if has_tool_call:
                        valid_messages.append(msg)
                    else:
                        logger.warning(f"Skipping orphaned tool message, as it has no preceding tool_call")
                else:
                    valid_messages.append(msg)
                    # Track if this message contains tool_calls
                    if msg["role"] == "assistant" and "tool_calls" in msg:
                        has_tool_call = True
                    else:
                        has_tool_call = False
            
            # Add the valid messages
            messages_for_api.extend(valid_messages)
            
            # Get AI response
            logger.info(f"Sending {len(messages_for_api)} messages to OpenAI API")
            ai_message = chat_completion(messages_for_api)
            
            # Extract content from response
            content = ai_message.choices[0].message.content
            
            # Fix the NoneType error with a proper check
            if content is None:
                content = ""  # Set empty string if content is None
                logger.info("Received empty content from OpenAI API, likely tool_calls only response")
            else:
                logger.info(f"Received response from OpenAI API: {content[:100]}..." if len(content) > 100 else content)
            
            # Check if the response contains tool calls - handle the case where tool_calls isn't an attribute
            has_tool_calls = False
            tool_calls = None
            
            try:
                tool_calls = ai_message.choices[0].message.tool_calls
                has_tool_calls = tool_calls is not None and len(tool_calls) > 0
            except (AttributeError, TypeError):
                # If the API response doesn't have tool_calls attribute, handle gracefully
                logger.info("No tool_calls attribute found in response")
                has_tool_calls = False
            
            if has_tool_calls:
                # Save assistant message with tool calls
                # Important: We don't emit this content to the chat as it may contain sequence details
                self.save_message("assistant", content, tool_calls=tool_calls)
                
                # Track if a sequence was generated
                sequence_generated = False
                sequence_data = None
                
                # For each tool call result, append to messages
                tool_results = []
                
                # Process tool calls
                for tool_call in tool_calls:
                    try:
                        logger.info(f"Processing tool call: {tool_call.function.name}")
                        
                        # Emit tool call start event
                        socketio.emit("tool_call_start", {
                            "tool": tool_call.function.name
                        }, room=self.session_id)
                        
                        # Parse arguments
                        args = json.loads(tool_call.function.arguments)
                        
                        # Call the appropriate tool
                        tool_result = handle_tool(tool_call.function.name, args)
                        
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": tool_call.function.name,
                            "result": tool_result
                        })
                        
                        logger.info(f"Tool {tool_call.function.name} executed successfully")
                        
                        # Emit tool call end event
                        socketio.emit("tool_call_end", {
                            "tool": tool_call.function.name,
                            "status": "success"
                        }, room=self.session_id)
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_call.function.name}: {e}", exc_info=True)
                        
                        # Create a human-readable error message
                        error_message = f"Error executing {tool_call.function.name}: {str(e)}"
                        
                        # Emit error event to client
                        socketio.emit("tool_call_error", {
                            "tool": tool_call.function.name,
                            "error": error_message
                        }, room=self.session_id)
                        
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": tool_call.function.name,
                            "result": {"error": error_message}
                        })
                
                # For each tool call result, append to messages
                for result in tool_results:
                    # Add tool result as a message from the tool
                    db = SessionLocal()
                    try:
                        tool_message = Message(
                            session_id=self.session_id,
                            user_id=self.user_id,
                            role="tool",
                            content=json.dumps(result["result"]),
                            tool_calls=None
                        )
                        db.add(tool_message)
                        db.commit()
                        
                        # Add to local messages
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": json.dumps(result["result"])
                        })
                    finally:
                        db.close()
                    
                    # If the tool is generating a sequence, send that to the client
                    if result["function_name"] == "generate_sequence":
                        sequence_generated = True
                        sequence_data = result["result"]
                        
                        # Log the actual result for debugging
                        logger.info(f"Sequence tool result type: {type(sequence_data).__name__}")
                        if isinstance(sequence_data, dict):
                            logger.info(f"Sequence data keys: {', '.join(sequence_data.keys())}")
                            if "steps" in sequence_data:
                                logger.info(f"Steps type: {type(sequence_data['steps']).__name__}, count: {len(sequence_data['steps']) if isinstance(sequence_data['steps'], list) else 'not a list'}")
                        
                        # More permissive validation - check if we at least have a dict we can work with
                        if isinstance(sequence_data, dict):
                            if "steps" not in sequence_data or not isinstance(sequence_data["steps"], list):
                                logger.warning("Fixing invalid sequence structure - adding steps array")
                                sequence_data["steps"] = sequence_data.get("steps", [])
                                if not isinstance(sequence_data["steps"], list):
                                    sequence_data["steps"] = []
                            
                            # Ensure other required fields exist
                            if "id" not in sequence_data or not sequence_data["id"]:
                                sequence_data["id"] = f"seq_{int(time.time())}"
                                
                            if "title" not in sequence_data or not sequence_data["title"]:
                                sequence_data["title"] = "Recruiting Sequence"
                                
                            if "target_role" not in sequence_data:
                                sequence_data["target_role"] = "Software Engineers"
                                
                            if "industry" not in sequence_data:
                                sequence_data["industry"] = "Technology"
                                
                            if "company" not in sequence_data:
                                sequence_data["company"] = "Your Company"
                            
                            logger.info(f"Valid sequence data generated/fixed with {len(sequence_data['steps'])} steps")
                            
                            # Make sure we've got sequence steps for outbound LinkedIn recruiting
                            if len(sequence_data['steps']) == 0:
                                # Create default steps if none exist
                                logger.info("No steps found in sequence data, creating default steps")
                                
                                sequence_data['steps'] = [
                                    {
                                        "id": f"step_{int(time.time())}_1",
                                        "step": 1,
                                        "day": 0,
                                        "channel": "LinkedIn",
                                        "subject": f"Opportunity for {sequence_data.get('target_role', 'professionals')}",
                                        "message": f"Hi [Name],\n\nI hope this message finds you well! I'm reaching out because your profile caught my attention. We're looking for talented {sequence_data.get('target_role', 'professionals')} at {sequence_data.get('company', 'our company')}.\n\nWould you be open to learning more about this opportunity?\n\nBest regards,\n[Your Name]",
                                        "timing": "Initial Outreach"
                                    }
                                ]
                            
                            # Save the sequence to database and emit update
                            try:
                                # First save to database
                                db = SessionLocal()
                                from api.models import Sequence
                                
                                # Check if we already have a sequence for this session
                                existing_sequence = db.query(Sequence).filter(
                                    Sequence.session_id == self.session_id
                                ).first()
                                
                                if existing_sequence:
                                    # Update existing sequence
                                    existing_sequence.title = sequence_data.get("title", "Recruiting Sequence")
                                    existing_sequence.target_role = sequence_data.get("target_role", "Professionals")
                                    existing_sequence.target_industry = sequence_data.get("industry", "Technology")
                                    existing_sequence.sequence_data = sequence_data
                                    db.commit()
                                    logger.info(f"Updated existing sequence {existing_sequence.id} for session {self.session_id}")
                                else:
                                    # Create new sequence
                                    new_sequence = Sequence(
                                        user_id=self.user_id,
                                        session_id=self.session_id,
                                        title=sequence_data.get("title", "Recruiting Sequence"),
                                        target_role=sequence_data.get("target_role", "Professionals"),
                                        target_industry=sequence_data.get("industry", "Technology"),
                                        sequence_data=sequence_data
                                    )
                                    db.add(new_sequence)
                                    db.commit()
                                    logger.info(f"Created new sequence for session {self.session_id}")
                            except Exception as db_error:
                                logger.error(f"Failed to save sequence to database: {str(db_error)}", exc_info=True)
                            finally:
                                db.close()
                            
                            # Now emit to websocket with retries
                            retry_count = 0
                            max_retries = 3
                            emit_success = False
                            
                            while not emit_success and retry_count < max_retries:
                                # Add delay between retries
                                if retry_count > 0:
                                    time.sleep(0.5)
                                    
                                retry_count += 1
                                logger.info(f"Emitting sequence_update (attempt {retry_count}/{max_retries})")
                                
                                # Use the utility function for reliable emission
                                emit_success = emit_sequence_update(self.session_id, sequence_data)
                                
                                if emit_success:
                                    logger.info("Successfully emitted sequence_update event")
                                else:
                                    logger.warning(f"Failed to emit sequence_update, retry {retry_count}/{max_retries}")
                            
                            if not emit_success:
                                logger.error("All attempts to emit sequence_update failed")
                                # Try direct socket emission as a last resort
                                try:
                                    socketio.emit("sequence_update", sequence_data, room=self.session_id)
                                    logger.info("Sent sequence_update via direct socketio.emit")
                                except Exception as sock_err:
                                    logger.error(f"Direct socket.emit failed: {str(sock_err)}")
                        else:
                            logger.error(f"Invalid sequence data format: {type(sequence_data)}")
                            socketio.emit("error", {
                                "message": "Generated sequence has invalid format"
                            }, room=self.session_id)
                
                # Get a follow-up message based on the tool results
                if sequence_generated:
                    # Create a message informing the user that a sequence has been created
                    # Don't include the entire sequence in the chat response
                    follow_up_message = (
                        f"I've created a recruiting sequence for {sequence_data.get('target_role', 'candidates')} "
                        f"in the {sequence_data.get('industry', 'specified')} industry. "
                        f"You can view and edit the sequence in the workspace panel on the right. "
                        f"The sequence includes {len(sequence_data.get('steps', []))} steps across different channels. "
                        f"Would you like to make any adjustments to the sequence?"
                    )
                    
                    # Save this message to the database
                    self.save_message("assistant", follow_up_message)
                    
                    # Emit this message to the chat
                    socketio.emit("chat_message", {
                        "role": "assistant",
                        "content": follow_up_message
                    }, room=self.session_id)
                    
                    # Emit event for tool call end
                    socketio.emit("tool_call_end", {}, room=self.session_id)
                    
                    return follow_up_message
                else:
                    # Add a special system prompt to guide the model's response
                    follow_up_prompt = get_sequence_followup_prompt(sequence_data)
                    messages_for_api.append({
                        "role": "system",
                        "content": follow_up_prompt
                    })
                
                    follow_up = chat_completion(messages_for_api)
                    follow_up_content = follow_up.choices[0].message.content
                    
                    # Save the follow-up message
                    self.save_message("assistant", follow_up_content)
                    
                    # Emit event for tool call end
                    socketio.emit("tool_call_end", {}, room=self.session_id)
                    
                    # Emit the follow-up message
                    socketio.emit("chat_message", {
                        "role": "assistant",
                        "content": follow_up_content
                    }, room=self.session_id)
                    
                    return follow_up_content
            else:
                # Save the assistant message
                self.save_message("assistant", content)
                
                # Emit message to websocket
                logger.info(f"Emitting assistant message to room {self.session_id}")
                socketio.emit("chat_message", {
                    "role": "assistant",
                    "content": content
                }, room=self.session_id)
                
                return content
        except Exception as e:
            error_msg = f"Error processing message: {e}"
            logger.error(error_msg, exc_info=True)
            
            # Emit error message to websocket
            socketio.emit("chat_message", {
                "role": "assistant",
                "content": f"I'm sorry, but I encountered an error processing your request. Technical details: {str(e)}"
            }, room=self.session_id)
            
            return error_msg
