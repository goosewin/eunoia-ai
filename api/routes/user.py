from flask import Blueprint, jsonify, request

from api.db import SessionLocal
from api.models import User

user_routes = Blueprint("user", __name__)

@user_routes.route("/api/user", methods=["GET"])
def get_user():
    user_id = request.args.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "company": user.company,
            "company_details": user.company_details,
            "created_at": user.created_at.isoformat()
        }
        
        return jsonify(user_data)
    finally:
        db.close()

@user_routes.route("/api/user", methods=["POST"])
def create_or_update_user():
    data = request.json
    required_fields = ["name", "email"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    
    db = SessionLocal()
    try:

        existing_user = db.query(User).filter(User.email == data["email"]).first()
        
        if existing_user:

            if "name" in data:
                existing_user.name = data["name"]
            if "company" in data:
                existing_user.company = data["company"]
            if "company_details" in data:
                existing_user.company_details = data["company_details"]
            
            db.commit()
            db.refresh(existing_user)
            
            user_data = {
                "id": existing_user.id,
                "name": existing_user.name,
                "email": existing_user.email,
                "company": existing_user.company,
                "company_details": existing_user.company_details,
                "created_at": existing_user.created_at.isoformat()
            }
            
            return jsonify(user_data)
        else:

            new_user = User(
                name=data["name"],
                email=data["email"],
                company=data.get("company", ""),
                company_details=data.get("company_details", "")
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            user_data = {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "company": new_user.company,
                "company_details": new_user.company_details,
                "created_at": new_user.created_at.isoformat()
            }
            
            return jsonify(user_data), 201
    finally:
        db.close() 
