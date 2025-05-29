from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS # Import Flask-CORS
import os

db = SQLAlchemy()
login_manager = LoginManager() 
login_manager.login_view = 'auth.login'

# This function will be used by Flask-Login to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    # Import models here to avoid circular imports if models.py imports db from this file
    from .models import User 
    return User.query.get(int(user_id))

def create_app(config_overrides=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Default Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/fire_equipment_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Ensuring JWT_SECRET_KEY is used, as it's what PyJWT expects if app.config['JWT_SECRET_KEY'] is used.
    # If auth.py uses os.environ.get('JWT_SECRET'), then .flaskenv should define JWT_SECRET.
    # For consistency with previous steps (test_config.py, auth.py), we'll use JWT_SECRET_KEY in app.config.
    # The .flaskenv file currently has JWT_SECRET. Let's ensure this is aligned or handled.
    # For now, will ensure app.config['JWT_SECRET_KEY'] is set.
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-placeholder') # Matches .flaskenv if it's JWT_SECRET there

    # Apply overrides for testing or other environments
    if config_overrides:
        app.config.update(config_overrides)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}}) # Initialize CORS

    from . import routes
    app.register_blueprint(routes.bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import api_routes
    app.register_blueprint(api_routes.api_bp)

    from . import admin_routes 
    app.register_blueprint(admin_routes.admin_bp)
    
    # Ensure models are imported. This can be done here or ensure blueprints import them.
    # from . import models # This line was commented out, it's good to ensure models are loaded.
                         # It's typically handled by models being imported in blueprint files (e.g., auth.py, api_routes.py)

    return app
