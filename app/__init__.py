from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_app():
    """
    Application factory for creating Flask app instance.
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.analyse import analyse_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analyse_bp)
    
    # Initialize database (stub for future MongoDB)
    # from app.models.db import init_db
    # init_db(app)
    
    return app
