import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from api.db import SessionLocal
from api.models import Message, Sequence, Session

session_routes = Blueprint("session", __name__)
logger = logging.getLogger(__name__)

@session_routes.route("/api/sessions", methods=["GET"])
def get_sessions():
    
    user_id = request.args.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    db = SessionLocal()
    try:
        sessions = db.query(Session).filter(
            Session.user_id == user_id
        ).order_by(Session.created_at.desc()).all()

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
    
    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.id == session_id
        ).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404

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
    
    data = request.json
    session_id = data.get("session_id")
    user_id = data.get("user_id")
    name = data.get("name", f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    
    db = SessionLocal()
    try:

        existing = db.query(Session).filter(Session.id == session_id).first()
        if existing:
            return jsonify({"error": "Session ID already exists", "id": session_id}), 400

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
    
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "name is required"}), 400
    
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404

        session.name = data["name"]
        session.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"Updated session {session_id} name to {data['name']}")
        
        return jsonify({
            "id": session.id,
            "name": session.name,
            "updated_at": session.updated_at.isoformat()
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating session: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@session_routes.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    
    db = SessionLocal()
    try:

        session = db.query(Session).filter(Session.id == session_id).first()
        
        if not session:
            return jsonify({"error": "Session not found"}), 404

        db.query(Message).filter(Message.session_id == session_id).delete()
        db.query(Sequence).filter(Sequence.session_id == session_id).delete()

        db.delete(session)
        db.commit()
        
        logger.info(f"Deleted session {session_id}")
        
        return jsonify({"message": "Session deleted successfully"})
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@session_routes.route("/api/sessions/fix-names", methods=["POST"])
def fix_empty_session_names():
    
    db = SessionLocal()
    try:

        empty_name_sessions = db.query(Session).filter(
            (Session.name == "") | (Session.name is None)
        ).all()
        
        fixed_count = 0

        for session in empty_name_sessions:

            first_message = db.query(Message).filter(
                Message.session_id == session.id,
                Message.role == "user"
            ).order_by(Message.created_at).first()
            
            if first_message:

                content = first_message.content
                truncated_content = content[:30].strip()
                new_name = truncated_content + ("..." if len(content) > 30 else "")

                session.name = new_name
                session.updated_at = datetime.now()
                fixed_count += 1
            else:

                session.name = f"Session {session.created_at.strftime('%Y-%m-%d')}"
                session.updated_at = datetime.now()
                fixed_count += 1

        db.commit()
        
        return jsonify({
            "message": f"Fixed {fixed_count} sessions with empty names",
            "fixed_count": fixed_count
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing session names: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 
