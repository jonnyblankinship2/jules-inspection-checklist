from flask import Blueprint, request, jsonify, current_app
from .models import User, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user as flask_login_current_user # Renamed to avoid conflict
import jwt 
import datetime
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# JWT_SECRET will be taken from app.config
# JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key') 

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required!'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists!'}), 400

    user = User(username=data['username'])
    user.set_password(data['password'])
    # Potentially set user.is_admin here if it's the first user or based on some logic
    # For now, new users are not admins by default as per model.
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required!'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password!'}), 401

    # Use Flask-Login to manage the session
    login_user(user) # Manages the user session

    # Create JWT token for API access (can be used alongside session for APIs)
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token expires in 24 hours
    }, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")

    return jsonify({'message': 'Logged in successfully.', 'token': token, 'user_id': user.id, 'username': user.username}), 200

# Decorator for token protected API routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            # Pass the user object to the decorated function, not just the ID
            # This aligns better with how Flask-Login's current_user works
            api_current_user = User.query.get(data['user_id'])
            if not api_current_user:
                return jsonify({'message': 'Token is invalid, user not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token processing error: {str(e)}'}), 401

        return f(api_current_user, *args, **kwargs) # Pass the correct user object: api_current_user
    return decorated
    
@auth_bp.route('/logout', methods=['POST']) # This logout is for API token invalidation (client-side) and session logout
@login_required # Protect with Flask-Login's session check for web context
def logout(): 
    # Flask-Login's logout_user handles session invalidation
    user_name = flask_login_current_user.username if flask_login_current_user.is_authenticated else "User"
    logout_user() # This will clear the Flask-Login session
    return jsonify({'message': f'{user_name} logged out successfully. Please discard the token if using API.'}), 200

@auth_bp.route('/status')
@login_required # Protected by Flask-Login session
def status():
    if flask_login_current_user.is_authenticated:
        return jsonify({
            'user_id': flask_login_current_user.id, 
            'username': flask_login_current_user.username, 
            'is_admin': flask_login_current_user.is_admin
        }), 200
    # This part is technically unreachable due to @login_required redirecting unauthenticated users
    return jsonify({'message': 'User not logged in'}), 401
