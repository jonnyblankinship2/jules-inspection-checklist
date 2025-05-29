from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return jsonify(message="Welcome to the Fire Equipment Checklist API!")

# Add more routes later for users, checklists, equipment
