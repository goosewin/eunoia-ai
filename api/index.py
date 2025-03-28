import os

import eventlet

eventlet.monkey_patch()  # Apply monkey patches for eventlet

from flask import Flask, jsonify
from flask_cors import CORS

from api.db import init_db
from api.routes import chat_routes, sequence_routes, session_routes, user_routes
from api.websocket import socketio

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(chat_routes)
app.register_blueprint(sequence_routes)
app.register_blueprint(session_routes)
app.register_blueprint(user_routes)

# Initialize WebSocket with CORS support
socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize database
with app.app_context():
    init_db()

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})

@app.route("/api/socket-test")
def socket_test():
    """Endpoint to test socket connection"""
    socketio.emit('test_event', {'message': 'This is a test event from the server'})
    return jsonify({"status": "Test event sent"})

if __name__ == "__main__":
    # Need to use 0.0.0.0 to make it accessible from outside the container
    print("Starting Eunoia API server with WebSocket support")
    socketio.run(app, debug=False, host='0.0.0.0', port=5328, allow_unsafe_werkzeug=True)
