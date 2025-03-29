import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from api.agent import Agent
from api.db import SessionLocal
from api.models import Message, Session

chat_routes = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)

active_agents = {}

@chat_routes.route("/api/chat", methods=["POST"])
async def send_message():
    try:
        data = request.json
        session_id = data.get("session_id")
        message = data.get("message")
        user_id = data.get("user_id")

        logger.info(f"Received message request: session_id={session_id}, message={message}, user_id={user_id}")

        if not session_id or not message:
            logger.warning(f"Missing required fields: session_id={session_id}, message={message}")
            return jsonify({"error": "session_id and message are required"}), 400

        if session_id not in active_agents:
            logger.info(f"Creating new agent for session {session_id}")
            active_agents[session_id] = Agent(session_id, user_id)
        
        agent = active_agents[session_id]

        logger.info(f"Processing message via agent for session {session_id}")
        response = await agent.process_message(message)
        
        logger.info(f"Completed processing message, response: {response[:100] if response else 'None'}...")
        return jsonify({
            "session_id": session_id,
            "response": response
        })
    except Exception as e:
        logger.error(f"Error processing message in route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@chat_routes.route("/api/chat/<session_id>", methods=["GET"])
def get_chat_history(session_id):

    db = SessionLocal()
    try:
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()

        messages_data = [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "tool_calls": message.tool_calls,
                "created_at": message.created_at.isoformat()
            }
            for message in messages
        ]
        
        return jsonify({
            "session_id": session_id,
            "messages": messages_data
        })
    finally:
        db.close()

@chat_routes.route("/api/chat/new", methods=["POST"])
def create_new_chat():
    data = request.json
    session_id = data.get("session_id") or str(uuid.uuid4())
    user_id = data.get("user_id")
    name = data.get("name", f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    db = SessionLocal()
    try:

        existing_session = db.query(Session).filter(Session.id == session_id).first()
        
        if not existing_session:

            new_session = Session(
                id=session_id,
                name=name,
                user_id=user_id
            )
            db.add(new_session)
            db.commit()
            logger.info(f"Created new session in database: {session_id}")
    except Exception as e:
        logger.error(f"Error creating session in database: {str(e)}")
        db.rollback()
    finally:
        db.close()

    active_agents[session_id] = Agent(session_id, user_id)
    
    return jsonify({
        "session_id": session_id,
        "name": name
    }) 
