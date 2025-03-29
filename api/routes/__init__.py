from flask import Blueprint, Flask, jsonify

from api.routes.chat import chat_routes
from api.routes.sequence import sequence_routes
from api.routes.session import session_routes
from api.routes.user import user_routes

config_routes = Blueprint("config", __name__)

@config_routes.route("/api/config", methods=["GET"])
def get_config():
    """Return UI configuration including copy and content"""
    return jsonify({
        "app_title": "EUNOIA AI",
        "app_subtitle": "AI Recruiting Assistant",
        "input_placeholder": "Type your message...",
        "welcome_message": (
            "Hi! I'm Eunoia, your AI recruiting assistant. "
            "What kind of recruiting campaign are you looking to run today?"
        )
    })

def init_routes(app: Flask):
    
    app.register_blueprint(chat_routes)
    app.register_blueprint(sequence_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(session_routes)
    app.register_blueprint(config_routes)

    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule} - {', '.join(rule.methods)}")
    
    print("API Routes:")
    for route in sorted(routes):
        print(f"  {route}") 

    return app
