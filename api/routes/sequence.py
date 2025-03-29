import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from flask import jsonify, request
from sqlalchemy.orm import Session

from api.db import SessionLocal, get_db
from api.models import Sequence, SequenceStep
from api.websocket import emit_sequence_update

router = APIRouter()

def create_response(success: bool = True, data: Any = None, error: str = None):
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    return response

def sequence_schema(sequence):
    if not sequence:
        return None
    
    return {
        "id": sequence.id,
        "name": sequence.name,
        "session_id": sequence.session_id,
        "description": sequence.description,
        "created_at": sequence.created_at.isoformat(),
        "updated_at": sequence.updated_at.isoformat(),
        "steps": [
            {
                "id": step.id,
                "channel": step.channel,
                "message": step.message,
                "position": step.position
            }
            for step in sorted(sequence.steps, key=lambda x: x.position)
        ]
    }

def validate_sequence_data(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Sequence data must be a dictionary"
    
    if "steps" not in data or not isinstance(data["steps"], list):
        return False, "Sequence must contain a 'steps' field that is a list"
    
    for step in data["steps"]:
        if not isinstance(step, dict):
            return False, "Each step must be a dictionary"
        if "message" not in step or not isinstance(step["message"], str):
            return False, "Each step must have a 'message' field that is a string"
        if "channel" not in step or not isinstance(step["channel"], str):
            return False, "Each step must have a 'channel' field that is a string"
    
    return True, ""

@router.get("/sequences/session")
async def get_sequence_for_session(session_id: str, db: Session = None):
    if db is None:
        db = get_db()
    
    if not session_id:
        return create_response(success=False, error="Missing session_id parameter")
    
    try:
        sequence = db.query(Sequence).filter(Sequence.session_id == session_id).first()
        
        if not sequence:
            return create_response(success=True, data={"sequence_data": None})
        
        sequence_data = sequence_schema(sequence)
        return create_response(success=True, data={"sequence_data": sequence_data})
    except Exception as e:
        logging.error(f"Error retrieving sequence for session {session_id}: {str(e)}")
        return create_response(success=False, error=f"Database error: {str(e)}")

async def save_or_update_sequence(
    request: Request,
    db: Session = None
):
    if db is None:
        db = get_db()
        
    try:
        data = await request.json()
        session_id = data.get("session_id")
        sequence_data = data.get("sequence")
        
        if not session_id:
            return create_response(success=False, error="Missing session_id")
        
        if not sequence_data:
            return create_response(success=False, error="Missing sequence data")
        
        is_valid, error_msg = validate_sequence_data(sequence_data)
        if not is_valid:
            return create_response(success=False, error=error_msg)
        
        existing_sequence = db.query(Sequence).filter(Sequence.session_id == session_id).first()
        
        if existing_sequence:
            existing_sequence.name = sequence_data.get("name", "Untitled Sequence")
            existing_sequence.description = sequence_data.get("description", "")
            existing_sequence.updated_at = datetime.utcnow()
            
            db.query(SequenceStep).filter(SequenceStep.sequence_id == existing_sequence.id).delete()
            
            for i, step in enumerate(sequence_data["steps"]):
                new_step = SequenceStep(
                    sequence_id=existing_sequence.id,
                    message=step["message"],
                    channel=step["channel"],
                    position=i
                )
                db.add(new_step)
            
            sequence_id = existing_sequence.id
        else:
            new_sequence = Sequence(
                session_id=session_id,
                name=sequence_data.get("name", "Untitled Sequence"),
                description=sequence_data.get("description", "")
            )
            db.add(new_sequence)
            db.flush()
            
            for i, step in enumerate(sequence_data["steps"]):
                new_step = SequenceStep(
                    sequence_id=new_sequence.id,
                    message=step["message"],
                    channel=step["channel"],
                    position=i
                )
                db.add(new_step)
            
            sequence_id = new_sequence.id
        
        db.commit()
        
        request.app.sio.emit(
            "sequence_update", 
            sequence_data,
            room=session_id
        )
        
        return create_response(success=True, data={"sequence_id": sequence_id})
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving sequence: {str(e)}")
        return create_response(success=False, error=f"Error saving sequence: {str(e)}")
    finally:
        db.close()

async def reset_sequence(
    request: Request,
    db: Session = None
):
    if db is None:
        db = get_db()
        
    try:
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            return create_response(success=False, error="Missing session_id")
        
        reset_success = await _reset_sequence_for_session(request, session_id, db)
        
        return create_response(success=True, data={"reset": reset_success})
    except Exception as e:
        db.rollback()
        logging.error(f"Error resetting sequence: {str(e)}")
        return create_response(success=False, error=f"Error resetting sequence: {str(e)}")
    finally:
        db.close()

async def _reset_sequence_for_session(request: Request, session_id: str, db: Session) -> bool:
    try:
        request.app.sio.emit(
            "sequence_update", 
            None,
            room=session_id
        )
        
        sequence = db.query(Sequence).filter(Sequence.session_id == session_id).first()
        if sequence:
            db.delete(sequence)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logging.error(f"Error in _reset_sequence_for_session: {str(e)}")
        raise

@router.route("/api/sequences", methods=["GET"])
def get_sequences():
    user_id = request.args.get("user_id")
    session_id = request.args.get("session_id")
    
    logger = logging.getLogger(__name__)
    logger.info(f"GET /api/sequences - user_id: {user_id}, session_id: {session_id}")
    
    if not user_id and not session_id:
        logger.warning("No user_id or session_id provided in request")
        return create_response(success=False, error="user_id or session_id is required")
    
    db = SessionLocal()
    try:
        query = db.query(Sequence)
        
        if user_id:
            query = query.filter(Sequence.user_id == user_id)
        if session_id:
            query = query.filter(Sequence.session_id == session_id)
            
        sequences = query.order_by(Sequence.created_at.desc()).all()
        logger.info(f"Found {len(sequences)} sequences for request")
        
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
        
        return create_response(success=True, data=sequence_data)
    except Exception as e:
        logger.error(f"Error retrieving sequences: {str(e)}", exc_info=True)
        return create_response(success=False, error=f"Database error: {str(e)}")
    finally:
        db.close()

@router.route("/api/sequences/<int:sequence_id>", methods=["GET"])
def get_sequence(sequence_id):
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.id == sequence_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
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

@router.route("/api/sequences", methods=["POST"])
def create_sequence():
    data = request.json
    required_fields = ["user_id", "title", "target_role", "target_industry", "sequence_data"]
    
    session_id = data.get("session_id")
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    db = SessionLocal()
    try:
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

@router.route("/api/sequences/<int:sequence_id>", methods=["PUT"])
def update_sequence(sequence_id):
    data = request.json
    
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.id == sequence_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
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

@router.route("/api/sequences/<int:sequence_id>", methods=["DELETE"])
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

@router.route("/api/sequences/session", methods=["PUT"])
def update_session_sequence():
    data = request.json
    required_fields = ["user_id", "title", "target_role", "target_industry", "sequence_data"]
    
    session_id = data.get("session_id")
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    db = SessionLocal()
    try:
        existing_sequence = db.query(Sequence).filter(
            Sequence.session_id == session_id
        ).first()
        
        if not existing_sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
        if "title" in data:
            existing_sequence.title = data["title"]
        if "target_role" in data:
            existing_sequence.target_role = data["target_role"]
        if "target_industry" in data:
            existing_sequence.target_industry = data["target_industry"]
        if "sequence_data" in data:
            existing_sequence.sequence_data = data["sequence_data"]
        
        existing_sequence.updated_at = datetime.now()
        db.commit()
        
        if existing_sequence.session_id and existing_sequence.sequence_data:
            emit_sequence_update(existing_sequence.session_id, existing_sequence.sequence_data)
        
        return jsonify({
            "id": existing_sequence.id,
            "message": "Sequence updated successfully"
        })
    finally:
        db.close()

@router.route("/api/sequences/session", methods=["DELETE"])
def delete_session_sequence():
    session_id = request.args.get("session_id")
    
    logger = logging.getLogger(__name__)
    logger.info(f"DELETE /api/sequences/session - session_id: {session_id}")
    
    if not session_id:
        logger.warning("No session_id provided in request")
        return jsonify({"error": "session_id is required"}), 400
    
    db = SessionLocal()
    try:
        sequence = db.query(Sequence).filter(
            Sequence.session_id == session_id
        ).first()
        
        if not sequence:
            return jsonify({"error": "Sequence not found"}), 404
        
        db.delete(sequence)
        db.commit()
        
        emit_sequence_update(session_id, None)
        
        return jsonify({
            "message": "Sequence deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting sequence: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        db.close() 
