import eventlet
from flask import jsonify

from api.app import create_app
from api.websocket import socketio

# Apply monkey patch after imports
eventlet.monkey_patch()

app = create_app()

socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from Flask!"})

@app.route("/api/socket-test")
def socket_test():
    
    socketio.emit('test_event', {'message': 'This is a test event from the server'})
    return jsonify({"status": "Test event sent"})

if __name__ == "__main__":

    print("Starting Eunoia API server with WebSocket support")
    socketio.run(app, debug=False, host='0.0.0.0', port=5328, allow_unsafe_werkzeug=True)
