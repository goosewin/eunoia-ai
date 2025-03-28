import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Dict, Optional, Set

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize socketio instance
socketio = SocketIO(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Keep track of clients in rooms
active_rooms: Dict[str, Set[str]] = {}
# Track sequence data per session
sequence_data: Dict[str, Any] = {}

@socketio.on('connect')
def handle_connect():
    """Handle new client connection"""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")
    
    # Clean up room membership
    for room_id, clients in list(active_rooms.items()):
        if client_id in clients:
            clients.remove(client_id)
            logger.info(f"Removed {client_id} from room {room_id}")
            
            # If room is empty, clean up sequence data
            if not clients:
                if room_id in sequence_data:
                    del sequence_data[room_id]
                    logger.info(f"Cleaned up sequence data for empty room {room_id}")
                
                del active_rooms[room_id]
                logger.info(f"Removed empty room {room_id}")

@socketio.on('error')
def handle_error(error):
    """Handle socket errors"""
    client_id = request.sid
    logger.error(f"Socket error from client {client_id}: {error}")
    emit('error', {'message': f'Error: {error}'}, room=client_id)

@socketio.on('join')
def on_join(data):
    """Join a specific chat session room"""
    client_id = request.sid
    session_id = data.get('session_id')
    
    if not session_id:
        logger.warning(f'Client {client_id} tried to join without session_id')
        emit('error', {'message': 'Missing session_id'}, room=client_id)
        return
    
    join_room(session_id)
    
    # Track clients in rooms
    if session_id not in active_rooms:
        active_rooms[session_id] = set()
    active_rooms[session_id].add(client_id)
    
    logger.info(f"Client {client_id} joined room: {session_id}")
    
    # Get the latest sequence from the database
    from api.db import SessionLocal
    from api.models import Sequence
    
    db = SessionLocal()
    try:
        # Query for the most recent sequence for this session
        latest_sequence = db.query(Sequence).filter(
            Sequence.session_id == session_id
        ).order_by(Sequence.created_at.desc()).first()
        
        # Always emit room_joined event first
        emit('room_joined', {'session_id': session_id})
        
        # Short delay to ensure client has processed room_joined event
        socketio.sleep(0.1)
        
        # If we found a sequence, emit it
        if latest_sequence and latest_sequence.sequence_data:
            logger.info(f"Found existing sequence {latest_sequence.id} for session {session_id}")
            emit('sequence_update', latest_sequence.sequence_data, room=client_id)
            
            # Also store sequence data for potential reconnects
            sequence_data[session_id] = latest_sequence.sequence_data
            
            logger.info(f"Emitted existing sequence data to new client in room {session_id}")
        else:
            logger.info(f"No existing sequence found in database for session {session_id}")
            
            # Check if we have sequence data in memory
            if session_id in sequence_data and sequence_data[session_id] is not None:
                logger.info(f"Using in-memory sequence data for session {session_id}")
                emit('sequence_update', sequence_data[session_id], room=client_id)
            else:
                logger.info(f"No sequence data available for session {session_id}")
                # Emit null sequence data to ensure client has clean state
                emit('sequence_update', None, room=client_id)
    except Exception as e:
        logger.error(f"Error fetching sequence in on_join: {str(e)}", exc_info=True)
        # Emit null sequence data as fallback
        emit('sequence_update', None, room=client_id)
    finally:
        db.close()

@socketio.on('leave')
def on_leave(data):
    """Leave a specific chat session room"""
    client_id = request.sid
    session_id = data.get('session_id')
    
    if session_id:
        leave_room(session_id)
        
        # Update room membership
        if session_id in active_rooms and client_id in active_rooms[session_id]:
            active_rooms[session_id].remove(client_id)
            
            # If room is empty, clean up sequence data
            if not active_rooms[session_id]:
                if session_id in sequence_data:
                    del sequence_data[session_id]
                
                del active_rooms[session_id]
                logger.info(f"Removed empty room {session_id}")
        
        logger.info(f"Client {client_id} left room: {session_id}")

@socketio.on('chat_message')
def handle_message(data):
    """Handle a new chat message from the client"""
    client_id = request.sid
    try:
        session_id = data.get('session_id')
        message = data.get('message')
        user_id = data.get('user_id')
        
        logger.info(f"Received chat_message from {client_id} in session {session_id}")
        
        if not session_id or not message:
            logger.warning(f'Client {client_id} sent invalid message data: {data}')
            socketio.emit('error', {'message': 'Invalid message data'}, room=client_id)
            return
        
        # Import agent here to avoid circular imports
        from api.agent import Agent
        from api.db import SessionLocal
        
        # Create or get agent for this session
        agent = Agent(session_id, user_id)
        
        # Acknowledge message receipt immediately
        socketio.emit('message_received', {'status': 'received', 'message': message}, room=client_id)
        
        logger.info(f"Processing message in session {session_id}: '{message[:50]}...' if len(message) > 50 else message")
        
        # Create a global reference to socketio and session for the background thread
        socketio_ref = socketio
        session_id_ref = session_id
        client_id_ref = client_id
        
        # Process the message asynchronously through the agent
        def process_message_task():
            try:
                import asyncio
                logger.info("Starting async processing in background thread")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process the message - the agent will use socketio reference
                logger.info(f"About to process message in agent: '{message[:50]}...' if len(message) > 50 else message")
                response = loop.run_until_complete(agent.process_message(message))
                logger.info(f"Agent processed message, length of response: {len(response) if response else 0}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Send error using socketio reference
                socketio_ref.emit('chat_message', {
                    'role': 'assistant',
                    'content': f"Error processing your message: {str(e)}"
                }, room=session_id_ref)
        
        # Start background thread for message processing
        thread = threading.Thread(target=process_message_task)
        thread.daemon = True
        thread.start()
        logger.info(f"Started background thread for processing message")
    except Exception as e:
        logger.error(f"Unexpected error in handle_message: {e}", exc_info=True)
        socketio.emit('error', {'message': f'Server error: {str(e)}'}, room=client_id)
        socketio.emit('chat_message', {
            'role': 'assistant',
            'content': f"I'm sorry, but I encountered an unexpected error: {str(e)}"
        }, room=client_id)

@socketio.on('new_session')
def handle_new_session(data):
    """Handle creating a new chat session"""
    client_id = request.sid
    session_id = data.get('session_id')
    
    if not session_id:
        logger.warning(f'Client {client_id} attempted to create session with invalid ID')
        emit('error', {'message': 'Invalid session ID'})
        return
        
    join_room(session_id)
    logger.info(f"New session created: {session_id}")
    
    # Initialize empty sequence data for new session
    sequence_data[session_id] = None
    
    # Connect to room without sending welcome message
    emit('chat_session_ready', {
        'session_id': session_id,
        'status': 'connected'
    }, room=session_id)

@socketio.on('sequence_edit')
def handle_sequence_edit(data):
    """Handle sequence edit from client"""
    client_id = request.sid
    session_id = data.get('session_id')
    sequence_id = data.get('sequence_id')
    changes = data.get('changes')
    
    if not session_id or not changes:
        logger.warning(f'Client {client_id} sent invalid sequence edit data')
        emit('error', {'message': 'Invalid sequence edit data'})
        return
    
    # Validate sequence data structure
    if not isinstance(changes, dict) or not changes.get('steps') or not isinstance(changes.get('steps'), list):
        logger.warning(f'Client {client_id} sent malformed sequence data')
        emit('error', {'message': 'Invalid sequence format. Required: steps array'})
        return
        
    logger.info(f"Sequence edit in session {session_id}")
    
    try:
        # Store the sequence data
        sequence_data[session_id] = changes
        
        # Acknowledge receipt
        emit('edit_received', {
            'status': 'received',
            'sequence_id': sequence_id
        }, room=client_id)
        
        # Broadcast the update to all clients in the room
        logger.info(f"Broadcasting sequence update to all clients in room {session_id}")
        emit('sequence_update', changes, room=session_id)
        
        # In production, changes would be saved to database via API endpoint
        # This WebSocket handler just handles real-time updates

    except Exception as e:
        logger.error(f"Error processing sequence edit: {e}", exc_info=True)
        emit('error', {'message': f'Error updating sequence: {str(e)}'}, room=client_id)

# Utility function that can be called from other modules
def emit_sequence_update(session_id: str, sequence_data_obj: Any) -> bool:
    """
    Reliable function to emit sequence update to clients
    Returns boolean indicating if emission was successful
    """
    try:
        logger.info(f"Emitting sequence_update to room {session_id}")
        
        # Handle the case when we want to clear sequence data (null/None case)
        if sequence_data_obj is None:
            logger.info(f"Clearing sequence data for session {session_id}")
            sequence_data[session_id] = None
            
            # Make sure we have clients in this room before emitting
            if session_id in active_rooms and active_rooms[session_id]:
                socketio.emit('sequence_update', None, room=session_id)
                logger.info(f"Successfully cleared sequence data for {len(active_rooms[session_id])} clients in room {session_id}")
                return True
            else:
                logger.warning(f"No clients in room {session_id} to receive sequence update")
                # Store the null data anyway for future connections
                sequence_data[session_id] = None
                return True  # Return success even if no clients - we've done our part
        
        # Convert the sequence_data_obj to a proper dictionary if it's not already
        sequence_dict = {}
        
        # If it's an object with attributes, convert to dict
        if hasattr(sequence_data_obj, '__dict__'):
            logger.info("Converting object with attributes to dictionary")
            sequence_dict = vars(sequence_data_obj)
        elif isinstance(sequence_data_obj, dict):
            logger.info("Using existing dictionary")
            sequence_dict = sequence_data_obj
        else:
            logger.error(f"Unsupported sequence data type: {type(sequence_data_obj)}")
            return False
            
        # Log detailed sequence info for debugging
        step_count = 0
        if 'steps' in sequence_dict and isinstance(sequence_dict['steps'], list):
            step_count = len(sequence_dict['steps'])
            logger.info(f"Sequence has {step_count} steps")
        else:
            logger.error("Could not find steps in sequence_data_obj or steps is not a list")
            
            # Try to ensure we have a steps list
            if 'steps' not in sequence_dict:
                sequence_dict['steps'] = []
            elif not isinstance(sequence_dict['steps'], list):
                sequence_dict['steps'] = []
        
        # Ensure minimal required fields exist
        if 'id' not in sequence_dict or not sequence_dict['id']:
            sequence_dict['id'] = f"seq_{int(time.time())}"
        
        if 'title' not in sequence_dict or not sequence_dict['title']:
            sequence_dict['title'] = "Recruiting Sequence"
            
        # Store sequence data for session - always do this even if no clients are connected
        sequence_data[session_id] = sequence_dict
        
        # Check if we should also save to database
        try:
            from api.db import SessionLocal
            from api.models import Sequence
            
            db = SessionLocal()
            
            # Check if sequence for this session already exists
            existing_sequence = db.query(Sequence).filter(
                Sequence.session_id == session_id
            ).order_by(Sequence.created_at.desc()).first()
            
            if existing_sequence:
                logger.info(f"Updating existing sequence {existing_sequence.id} for session {session_id}")
                # Update existing sequence
                existing_sequence.sequence_data = sequence_dict
                db.commit()
            else:
                logger.info(f"Saving new sequence for session {session_id}")
                # Create new sequence record
                new_sequence = Sequence(
                    user_id=1,  # Default user ID - replace with actual if available
                    session_id=session_id,
                    title=sequence_dict.get('title', 'Recruiting Sequence'),
                    target_role=sequence_dict.get('target_role', 'Candidates'),
                    target_industry=sequence_dict.get('industry', 'Technology'),
                    sequence_data=sequence_dict
                )
                db.add(new_sequence)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error saving sequence to database: {str(db_error)}", exc_info=True)
        finally:
            db.close()
            
        # Make sure we have clients in this room before emitting
        if session_id not in active_rooms or not active_rooms[session_id]:
            logger.warning(f"No clients in room {session_id} to receive sequence update")
            return True  # We've stored the data in memory and DB, so return success
            
        # Emit to clients in the room
        socketio.emit('sequence_update', sequence_dict, room=session_id)
        logger.info(f"Successfully emitted sequence_update to {len(active_rooms[session_id])} clients in room {session_id}")
        
        # Also emit to each client individually as a fallback mechanism
        for client_id in active_rooms[session_id]:
            try:
                # Short delay between emissions to prevent socket buffer overflow
                socketio.sleep(0.05)
                logger.info(f"Sending individual sequence update to client {client_id}")
                socketio.emit('sequence_update', sequence_dict, room=client_id)
            except Exception as inner_e:
                logger.error(f"Error sending to client {client_id}: {str(inner_e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error emitting sequence update: {str(e)}", exc_info=True)
        return False 
