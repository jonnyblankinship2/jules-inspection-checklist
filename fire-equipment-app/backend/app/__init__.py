from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager # Import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager() # Initialize LoginManager
login_manager.login_view = 'auth.login' # Specify the login view; 'auth.login' assumes your login route is in auth_bp

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
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-placeholder')

    # Apply overrides for testing or other environments
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    login_manager.init_app(app) # Initialize LoginManager with the app
    Migrate(app, db) # Initialize Flask-Migrate here after db and app are configured

    from . import routes 
    app.register_blueprint(routes.bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import api_routes
    app.register_blueprint(api_routes.api_bp)

    from . import admin_routes # Import the new admin routes
    app.register_blueprint(admin_routes.admin_bp) # Register the new admin blueprint
    
    # Ensure models are imported so Flask-Migrate can see them
    # This import is implicitly handled if models are imported within blueprints or here directly
    # from . import models 

    return app
