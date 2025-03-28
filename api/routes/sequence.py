import json
import logging
import random
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from api.db import SessionLocal, get_db
from api.models import Sequence

sequence_routes = Blueprint("sequence", __name__)

@sequence_routes.route("/api/sequences", methods=["GET"])
def get_sequences():
    user_id = request.args.get("user_id")
    session_id = request.args.get("session_id")
    
    logger = logging.getLogger(__name__)
    logger.info(f"GET /api/sequences - user_id: {user_id}, session_id: {session_id}")
    
    if not user_id and not session_id:
        logger.warning("No user_id or session_id provided in request")
        return jsonify({"error": "user_id or session_id is required"}), 400
    
    db = SessionLocal()
    try:
        # Base query
        query = db.query(Sequence)
        
        # Apply filters
        if user_id:
            query = query.filter(Sequence.user_id == user_id)
        if session_id:
            query = query.filter(Sequence.session_id == session_id)
            
        sequences = query.order_by(Sequence.created_at.desc()).all()
        logger.info(f"Found {len(sequences)} sequences for request")
        
        # Convert to dictionary format for client
        sequence_data = [
            {
                "id": seq.id,
                "user_id": seq.user_id,
                "session_id": seq.session_id,
                "title": seq.title,
                "target_role": seq.target_role,
                "target_industry": seq.target_industry,
                "created_at": seq.created_at.isoformat()
            }
            for seq in sequences
        ]
        
        return jsonify(sequence_data)
    except Exception as e:
        logger.error(f"Error retrieving sequences: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        db.close()

@sequence_routes.route("/api/sequences/<int:sequence_id>", methods=["GET"])
def get_sequence(sequence_id):
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.id == sequence_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
        # Convert to dictionary format for client
        sequence_data = {
            "id": sequence.id,
            "user_id": sequence.user_id,
            "session_id": sequence.session_id,
            "title": sequence.title,
            "target_role": sequence.target_role,
            "target_industry": sequence.target_industry,
            "sequence_data": sequence.sequence_data,
            "created_at": sequence.created_at.isoformat(),
            "updated_at": sequence.updated_at.isoformat()
        }
        
        return jsonify(sequence_data)
    finally:
        db.close()

@sequence_routes.route("/api/sequences", methods=["POST"])
def create_sequence():
    data = request.json
    required_fields = ["user_id", "title", "target_role", "target_industry", "sequence_data"]
    
    # Also handle session_id if provided
    session_id = data.get("session_id")
    
    # Validate required fields
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    db = SessionLocal()
    try:
        # Create new sequence in database
        new_sequence = Sequence(
            user_id=data["user_id"],
            session_id=session_id,
            title=data["title"],
            target_role=data["target_role"],
            target_industry=data["target_industry"],
            sequence_data=data["sequence_data"]
        )
        
        db.add(new_sequence)
        db.commit()
        db.refresh(new_sequence)
        
        # Convert to dictionary format for client
        sequence_data = {
            "id": new_sequence.id,
            "user_id": new_sequence.user_id,
            "session_id": new_sequence.session_id,
            "title": new_sequence.title,
            "target_role": new_sequence.target_role,
            "target_industry": new_sequence.target_industry,
            "created_at": new_sequence.created_at.isoformat(),
            "updated_at": new_sequence.updated_at.isoformat()
        }
        
        return jsonify(sequence_data), 201
    finally:
        db.close()

@sequence_routes.route("/api/sequences/<int:sequence_id>", methods=["PUT"])
def update_sequence(sequence_id):
    data = request.json
    
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.id == sequence_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
        # Update fields
        if "title" in data:
            sequence.title = data["title"]
        if "target_role" in data:
            sequence.target_role = data["target_role"]
        if "target_industry" in data:
            sequence.target_industry = data["target_industry"]
        if "sequence_data" in data:
            sequence.sequence_data = data["sequence_data"]
        if "session_id" in data:
            sequence.session_id = data["session_id"]
        
        sequence.updated_at = datetime.now()
        db.commit()
        
        return jsonify({
            "id": sequence.id,
            "message": "Sequence updated successfully"
        })
    finally:
        db.close()

@sequence_routes.route("/api/sequences/<int:sequence_id>", methods=["DELETE"])
def delete_sequence(sequence_id):
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.id == sequence_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
        db.delete(sequence)
        db.commit()
        
        return jsonify({
            "message": "Sequence deleted successfully"
        })
    finally:
        db.close()

@sequence_routes.route("/api/sequences/reset", methods=["POST"])
def reset_sequence():
    """Clear all sequence data for a session - typically used when starting a new session"""
    data = request.json
    session_id = data.get("session_id")
    
    logger = logging.getLogger(__name__)
    logger.info(f"POST /api/sequences/reset - session_id: {session_id}")
    
    if not session_id:
        logger.warning("No session_id provided in reset request")
        return jsonify({"error": "session_id is required"}), 400
    
    # This endpoint doesn't actually delete anything from the database
    # It just serves as a trigger for WebSocket notifications to clear UI state
    
    # If using WebSockets, emit an event to clear sequence data
    try:
        logger.info(f"Attempting to reset sequence data for session: {session_id}")
        from api.websocket import emit_sequence_update, socketio
        
        # Use the dedicated function for reliable updates
        success = emit_sequence_update(session_id, None)
        
        if success:
            logger.info(f"Successfully reset sequence data for session: {session_id}")
            return jsonify({"status": "success", "message": "Sequence data reset"}), 200
        else:
            logger.warning(f"Failed to reset sequence data for session: {session_id}")
            return jsonify({"status": "warning", "message": "Sequence data reset may not have reached all clients"}), 200
            
    except ImportError as e:
        logger.error(f"WebSockets not available: {str(e)}")
        # WebSockets not available, still return success
        return jsonify({"status": "success", "message": "Sequence data reset (no WebSocket)"}), 200
    except Exception as e:
        logger.error(f"Error resetting sequence data: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500 
