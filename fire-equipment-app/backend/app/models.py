from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Import UserMixin

class User(db.Model, UserMixin): # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) # Store hashed passwords
    role = db.Column(db.String(50), default='firefighter') # e.g., firefighter, admin
    is_admin = db.Column(db.Boolean, default=False) # New field for admin status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50)) # e.g., 'SCBA', 'Hose', 'Truck Main'
    # Link to a specific truck/apparatus if needed
    # apparatus_id = db.Column(db.Integer, db.ForeignKey('apparatus.id')) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Equipment {self.name}>'

class ChecklistTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # e.g., 'Daily Engine Check', 'Monthly SCBA'
    type = db.Column(db.String(50), nullable=False) # 'daily', 'weekly', 'monthly'
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('ChecklistItemTemplate', backref='checklist_template', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ChecklistTemplate {self.name}>'

class ChecklistItemTemplate(db.Model): # Defines what items are in a template
    id = db.Column(db.Integer, primary_key=True)
    checklist_template_id = db.Column(db.Integer, db.ForeignKey('checklist_template.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True) # Optional, some checks might not be for specific equipment
    item_description = db.Column(db.String(255), nullable=False) # e.g., "Check tire pressure", "Ensure PASS device operational"
    expected_status = db.Column(db.String(100), nullable=True) # e.g., "Operational", "Full"

class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    checklist_template_id = db.Column(db.Integer, db.ForeignKey('checklist_template.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='completed') # e.g., 'in_progress', 'completed'
    notes = db.Column(db.Text, nullable=True) # Overall notes for the checklist

    user = db.relationship('User', backref='checklists')
    template = db.relationship('ChecklistTemplate')
    items = db.relationship('ChecklistItemInstance', backref='checklist', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Checklist ID: {self.id} by User: {self.user_id} on {self.completed_at.strftime("%Y-%m-%d")}>'

class ChecklistItemInstance(db.Model): # Actual instance of a check
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True) # Denormalized for easier querying, or from ChecklistItemTemplate
    item_description_from_template = db.Column(db.String(255)) # Copied from template
    status = db.Column(db.String(50), nullable=False) # e.g., 'checked', 'broken', 'missing', 'needs_repair'
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    equipment = db.relationship('Equipment', backref='checklist_items')
    
    def __repr__(self):
        return f'<ChecklistItemInstance ID: {self.id} for Checklist: {self.checklist_id} - Status: {self.status}>'
