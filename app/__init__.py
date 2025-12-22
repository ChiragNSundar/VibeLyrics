"""
VibeLyrics Flask Application Factory
"""
from flask import Flask
from .config import Config
from .models.database import db

from flask_socketio import SocketIO

# Initialize SocketIO globally
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Handle both config class and dict
    if isinstance(config_class, dict):
        app.config.from_object(Config)
        app.config.update(config_class)
    else:
        app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    socketio.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from .routes.workspace import workspace_bp
    from .routes.journal import journal_bp
    from .routes.references import references_bp
    from .routes.settings import settings_bp
    from .routes.api import api_bp
    from .routes.education import education_bp
    
    app.register_blueprint(workspace_bp)
    app.register_blueprint(journal_bp, url_prefix="/journal")
    app.register_blueprint(references_bp, url_prefix="/references")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(education_bp, url_prefix="/education")
    
    # Import socket events to register them
    from . import events
    
    return app
