from flask import Blueprint, render_template
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def dashboard():
    # This is a basic placeholder. 
    # In a real application, you'd add checks here to ensure current_user.is_admin
    # For now, just being logged in is enough to see this page.
    # More granular access control for specific admin actions will be needed later.
    return render_template('admin/index.html', title='Admin Dashboard')
