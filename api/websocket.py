import logging
import threading
import time
from typing import Any

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

active_rooms: dict[str, set[str]] = {}

sequence_data: dict[str, Any] = {}

@socketio.on('connect')
def handle_connect():
    
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")

    for room_id, clients in list(active_rooms.items()):
        if client_id in clients:
            clients.remove(client_id)
            logger.info(f"Removed {client_id} from room {room_id}")

            if not clients:
                if room_id in sequence_data:
                    del sequence_data[room_id]
                    logger.info(f"Cleaned up sequence data for empty room {room_id}")
                
                del active_rooms[room_id]
                logger.info(f"Removed empty room {room_id}")

@socketio.on('error')
def handle_error(error):
    
    client_id = request.sid
    logger.error(f"Socket error from client {client_id}: {error}")
    emit('error', {'message': f'Error: {error}'}, room=client_id)

@socketio.on('join')
def on_join(data):
    
    client_id = request.sid
    session_id = data.get('session_id')
    
    if not session_id:
        logger.warning(f'Client {client_id} tried to join without session_id')
        emit('error', {'message': 'Missing session_id'}, room=client_id)
        return
    
    join_room(session_id)

    if session_id not in active_rooms:
        active_rooms[session_id] = set()
    active_rooms[session_id].add(client_id)
    
    logger.info(f"Client {client_id} joined room: {session_id}")

    from api.db import SessionLocal
    from api.models import Sequence
    
    db = SessionLocal()
    try:

        latest_sequence = db.query(Sequence).filter(
            Sequence.session_id == session_id
        ).order_by(Sequence.created_at.desc()).first()

        emit('room_joined', {'session_id': session_id})

        socketio.sleep(0.1)

        if latest_sequence and latest_sequence.sequence_data:
            logger.info(f"Found existing sequence {latest_sequence.id} for session {session_id}")
            emit('sequence_update', latest_sequence.sequence_data, room=client_id)

            sequence_data[session_id] = latest_sequence.sequence_data
            
            logger.info(f"Emitted existing sequence data to new client in room {session_id}")
        else:
            logger.info(f"No existing sequence found in database for session {session_id}")

            if session_id in sequence_data and sequence_data[session_id] is not None:
                logger.info(f"Using in-memory sequence data for session {session_id}")
                emit('sequence_update', sequence_data[session_id], room=client_id)
            else:
                logger.info(f"No sequence data available for session {session_id}")

                emit('sequence_update', None, room=client_id)
    except Exception as e:
        logger.error(f"Error fetching sequence in on_join: {str(e)}", exc_info=True)

        emit('sequence_update', None, room=client_id)
    finally:
        db.close()

@socketio.on('leave')
def on_leave(data):
    
    client_id = request.sid
    session_id = data.get('session_id')
    
    if session_id:
        leave_room(session_id)

        if session_id in active_rooms and client_id in active_rooms[session_id]:
            active_rooms[session_id].remove(client_id)

            if not active_rooms[session_id]:
                if session_id in sequence_data:
                    del sequence_data[session_id]
                
                del active_rooms[session_id]
                logger.info(f"Removed empty room {session_id}")
        
        logger.info(f"Client {client_id} left room: {session_id}")

@socketio.on('chat_message')
def handle_message(data):
    
    client_id = request.sid
    try:
        session_id = data.get('session_id')
        message = data.get('message')
        user_id = data.get('user_id')
        
        logger.info(f"Received chat_message from {client_id} in session {session_id}")
        
        if not session_id or not message:
            logger.warning(f'Client {client_id} sent invalid message data: {data}')
            emit('error', {'message': 'Invalid message data'}, room=client_id)
            return

        from api.agent import Agent

        agent = Agent(session_id, user_id)

        emit('message_received', {'status': 'received', 'message': message}, room=client_id)
        
        logger.info(f"Processing message in session {session_id}: '{message[:50]}...' if len(message) > 50 else message")

        def process_message_task():
            try:
                import asyncio
                logger.info("Starting async processing in background thread")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                response = loop.run_until_complete(agent.process_message(message))
                logger.info(f"Agent processed message, length of response: {len(response) if response else 0}")

                socketio.emit('chat_message', {
                    'role': 'assistant',
                    'content': response
                }, room=session_id)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

                socketio.emit('chat_message', {
                    'role': 'assistant',
                    'content': f"I encountered an error processing your request: {str(e)}"
                }, room=session_id)

                socketio.emit('error', {
                    'message': f"Error processing message: {str(e)}"
                }, room=session_id)
            finally:

                socketio.emit('processing_complete', {}, room=session_id)

        threading.Thread(target=process_message_task).start()
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        emit('error', {'message': f'Server error: {str(e)}'}, room=client_id)

@socketio.on('sequence_edit')
def handle_sequence_edit(data):
    
    client_id = request.sid
    try:
        session_id = data.get('session_id')
        sequence_id = data.get('sequence_id')
        changes = data.get('changes')
        
        if not session_id or not sequence_id or not changes:
            logger.warning(f'Client {client_id} sent invalid sequence edit data')
            emit('error', {'message': 'Invalid sequence edit data'}, room=client_id)
            return
        
        logger.info(f"Processing sequence edit in session {session_id} for sequence {sequence_id}")

        from api.db import SessionLocal
        from api.models import Sequence
        
        db = SessionLocal()
        try:

            sequence = db.query(Sequence).filter(
                Sequence.id == sequence_id,
                Sequence.session_id == session_id
            ).first()
            
            if not sequence:
                logger.warning(f"Sequence {sequence_id} not found for session {session_id}")
                emit('error', {'message': f'Sequence {sequence_id} not found'}, room=client_id)
                return

            sequence.sequence_data = changes
            sequence.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
            db.commit()
            
            logger.info(f"Saved sequence edit for {sequence_id}")

            sequence_data[session_id] = changes

            emit('sequence_update', changes, room=session_id)
            
        except Exception as e:
            logger.error(f"Error saving sequence edit: {e}", exc_info=True)
            db.rollback()
            emit('error', {'message': f'Error saving sequence: {str(e)}'}, room=client_id)
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in handle_sequence_edit: {e}", exc_info=True)
        emit('error', {'message': f'Server error: {str(e)}'}, room=client_id)

def emit_sequence_update(session_id: str, sequence: dict[str, Any]):
    
    if not session_id:
        logger.warning(f"Invalid session_id for emit_sequence_update: {session_id}")
        return False
    
    if not sequence:
        logger.warning(f"Invalid sequence data for emit_sequence_update in session {session_id}")

        try:
            socketio.emit('sequence_update', None, room=session_id)
            logger.info(f"Emitted null sequence_update to reset clients in session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error emitting null sequence_update: {e}", exc_info=True)
            return False

    if "steps" not in sequence:
        logger.error(f"Sequence missing steps array in session {session_id}")
        sequence["steps"] = []
    
    if not isinstance(sequence["steps"], list):
        logger.error(f"Sequence steps is not an array in session {session_id}")
        sequence["steps"] = []

    if "session_id" not in sequence:
        sequence["session_id"] = session_id

    sequence_data[session_id] = sequence
    
    logger.info(f"Emitting sequence_update for session {session_id} with {len(sequence['steps'])} steps")

    socketio.sleep(0.2)
    
    try:
        socketio.emit('sequence_update', sequence, room=session_id)
        logger.info(f"Successfully emitted sequence_update with {len(sequence.get('steps', []))} steps")
        return True
    except Exception as e:
        logger.error(f"Error emitting sequence_update: {e}", exc_info=True)
        return False

def emit_tool_call_start(session_id: str, tool_name: str):
    
    try:
        socketio.emit('tool_call_start', {'tool': tool_name}, room=session_id)
        logger.info(f"Emitted tool_call_start for {tool_name} in session {session_id}")
    except Exception as e:
        logger.error(f"Error emitting tool_call_start: {e}", exc_info=True)

def emit_tool_call_end(session_id: str):
    
    try:
        socketio.emit('tool_call_end', {}, room=session_id)
        logger.info(f"Emitted tool_call_end in session {session_id}")
    except Exception as e:
        logger.error(f"Error emitting tool_call_end: {e}", exc_info=True)

def emit_tool_call_error(session_id: str, tool_name: str, error: str):
    
    try:
        socketio.emit('tool_call_error', {'tool': tool_name, 'error': error}, room=session_id)
        logger.info(f"Emitted tool_call_error for {tool_name} in session {session_id}: {error}")
    except Exception as e:
        logger.error(f"Error emitting tool_call_error: {e}", exc_info=True) 
