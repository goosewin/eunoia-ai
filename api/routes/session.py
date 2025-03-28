import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from api.db import SessionLocal
from api.models import Sequence, Session

session_routes = Blueprint("session", __name__)
logger = logging.getLogger(__name__)

@session_routes.route("/api/sessions", methods=["GET"])
def get_sessions():
    """Get all sessions for a user"""
    user_id = request.args.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    db = SessionLocal()
    try:
        sessions = db.query(Session).filter(
            Session.user_id == user_id
        ).order_by(Session.created_at.desc()).all()
        
        # Convert to dictionary format for client
        session_data = [
            {
                "id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            for session in sessions
        ]
        
        return jsonify(session_data)
    finally:
        db.close()

@session_routes.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """Get a specific session by ID"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.id == session_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Get sequences linked to this session
        sequences = db.query(Sequence).filter(
            Sequence.session_id == session_id
        ).all()
        
        sequence_data = [
            {
                "id": seq.id,
                "title": seq.title,
                "target_role": seq.target_role,
                "target_industry": seq.target_industry,
                "created_at": seq.created_at.isoformat()
            }
            for seq in sequences
        ]
        
        # Convert to dictionary format for client
        session_data = {
            "id": session.id,
            "name": session.name,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "sequences": sequence_data
        }
        
        return jsonify(session_data)
    finally:
        db.close()

@session_routes.route("/api/sessions", methods=["POST"])
def create_session():
    """Create a new session"""
    data = request.json
    session_id = data.get("session_id")
    user_id = data.get("user_id")
    name = data.get("name", f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    
    db = SessionLocal()
    try:
        # Check if session already exists
        existing = db.query(Session).filter(Session.id == session_id).first()
        if existing:
            return jsonify({"error": "Session ID already exists", "id": session_id}), 400
        
        # Create new session
        new_session = Session(
            id=session_id,
            name=name,
            user_id=user_id
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"Created new session: {session_id}")
        
        return jsonify({
            "id": new_session.id,
            "name": new_session.name,
            "created_at": new_session.created_at.isoformat(),
            "updated_at": new_session.updated_at.isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@session_routes.route("/api/sessions/<session_id>", methods=["PUT"])
def update_session(session_id):
    """Update a session (rename)"""
    data = request.json
    name = data.get("name")
    
    if not name:
        return jsonify({"error": "name is required"}), 400
    
    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.id == session_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Update name
        session.name = name
        session.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"Renamed session {session_id} to '{name}'")
        
        return jsonify({
            "id": session.id,
            "name": session.name,
            "updated_at": session.updated_at.isoformat(),
            "message": "Session updated successfully"
        })
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 
