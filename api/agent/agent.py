import logging
import os
import time

from openai import OpenAI

from api.db.database import get_db
from api.db.models import Sequence

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = os.environ.get("MODEL_NAME", "gpt-4o")
        
    def get_completion(self, messages, functions=None, function_call="auto"):
        try:
            if functions:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=[{"type": "function", "function": fn} for fn in functions],
                    tool_choice=function_call
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            
            return response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None

def handle_generate_sequence_result(app, session_id, result):
    
    if not result or not isinstance(result, dict):
        logger.error(f"Invalid sequence result format: {result}")
        return False
    
    try:
        sequence_data = result.get("sequence")
        
        if not sequence_data or not isinstance(sequence_data, dict):
            logger.error(f"Missing or invalid sequence_data: {sequence_data}")
            return False
            
        if "steps" not in sequence_data or not isinstance(sequence_data["steps"], list):
            logger.error("Sequence is missing steps array or steps is not a list")
            return False
            
        steps = sequence_data.get("steps", [])
        logger.info(f"Generated sequence with {len(steps)} steps")
        
        db = next(get_db())
        try:

            existing_sequence = db.query(Sequence).filter(Sequence.session_id == session_id).first()
            
            if existing_sequence:

                existing_sequence.sequence_data = sequence_data
                existing_sequence.updated_at = time.time()
                db.commit()
                logger.info(f"Updated existing sequence for session {session_id}")
            else:

                new_sequence = Sequence(
                    session_id=session_id,
                    title=sequence_data.get("title", "Untitled Sequence"),
                    sequence_data=sequence_data
                )
                db.add(new_sequence)
                db.commit()
                logger.info(f"Created new sequence for session {session_id}")

            max_retries = 3
            for i in range(max_retries):
                try:
                    app.sio.emit("sequence_update", sequence_data, room=session_id)
                    logger.info(f"Emitted sequence_update to session {session_id}")
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        logger.warning(f"Error emitting sequence update (retry {i+1}/{max_retries}): {e}")
                        time.sleep(0.5)
                    else:
                        logger.error(f"Failed to emit sequence update after {max_retries} retries: {e}")
                        return False
            
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in handle_generate_sequence_result: {str(e)}")
            return False
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in handle_generate_sequence_result: {str(e)}")
        return False

def handle_tool_result(app, session_id, tool_name, result):
    
    if tool_name == "generate_sequence" and result:
        return handle_generate_sequence_result(app, session_id, result)
    return False
