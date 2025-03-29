from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from api.routes import init_routes
    init_routes(app)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Server error'}), 500

    from api.db import init_db
    init_db()
    
    return app 
