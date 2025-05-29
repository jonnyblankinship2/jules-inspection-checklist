from flask import Blueprint, request, jsonify
from .models import db, Equipment, ChecklistTemplate, ChecklistItemTemplate, Checklist, ChecklistItemInstance, User
from .auth import token_required # To protect routes
import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# == Equipment Management ==
@api_bp.route('/equipment', methods=['POST'])
@token_required
def create_equipment(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Equipment name is required'}), 400
    
    # Optional: Add check for admin role here if roles are implemented
    # if current_user.role != 'admin':
    #     return jsonify({'message': 'Cannot perform that function!'}), 403

    new_equipment = Equipment(
        name=data['name'],
        description=data.get('description'),
        category=data.get('category')
    )
    db.session.add(new_equipment)
    db.session.commit()
    return jsonify({'message': 'Equipment created', 'id': new_equipment.id}), 201

@api_bp.route('/equipment', methods=['GET'])
@token_required
def get_all_equipment(current_user):
    equipments = Equipment.query.all()
    output = []
    for eq in equipments:
        output.append({
            'id': eq.id, 
            'name': eq.name, 
            'description': eq.description, 
            'category': eq.category
        })
    return jsonify({'equipment': output})

@api_bp.route('/equipment/<int:equipment_id>', methods=['GET'])
@token_required
def get_equipment(current_user, equipment_id):
    eq = Equipment.query.get_or_404(equipment_id)
    return jsonify({
        'id': eq.id, 
        'name': eq.name, 
        'description': eq.description, 
        'category': eq.category
    })

@api_bp.route('/equipment/<int:equipment_id>', methods=['PUT'])
@token_required
def update_equipment(current_user, equipment_id):
    # Optional: Add check for admin role here
    eq = Equipment.query.get_or_404(equipment_id)
    data = request.get_json()
    eq.name = data.get('name', eq.name)
    eq.description = data.get('description', eq.description)
    eq.category = data.get('category', eq.category)
    db.session.commit()
    return jsonify({'message': 'Equipment updated'})

@api_bp.route('/equipment/<int:equipment_id>', methods=['DELETE'])
@token_required
def delete_equipment(current_user, equipment_id):
    # Optional: Add check for admin role here
    eq = Equipment.query.get_or_404(equipment_id)
    db.session.delete(eq)
    db.session.commit()
    return jsonify({'message': 'Equipment deleted'})

# == Checklist Template Management ==
@api_bp.route('/checklist-templates', methods=['POST'])
@token_required
def create_checklist_template(current_user):
    data = request.get_json()
    if not data or not data.get('name') or not data.get('type') or not data.get('items'):
        return jsonify({'message': 'Missing required fields: name, type, items'}), 400
    
    # Optional: Add check for admin role here

    new_template = ChecklistTemplate(
        name=data['name'],
        type=data['type'],
        description=data.get('description')
    )
    db.session.add(new_template)
    # Process items
    for item_data in data['items']:
        if not item_data.get('item_description'):
            db.session.rollback() # Rollback if an item is invalid
            return jsonify({'message': 'item_description is required for all items'}), 400
        
        item_template = ChecklistItemTemplate(
            # checklist_template_id will be set by SQLAlchemy relationship append below
            item_description=item_data['item_description'],
            expected_status=item_data.get('expected_status'),
            equipment_id=item_data.get('equipment_id') # Ensure this equipment exists if provided
        )
        if item_data.get('equipment_id') and not Equipment.query.get(item_data.get('equipment_id')):
            db.session.rollback()
            return jsonify({'message': f"Equipment with ID {item_data.get('equipment_id')} not found"}), 400
        new_template.items.append(item_template)
    
    db.session.commit()
    return jsonify({'message': 'Checklist template created', 'id': new_template.id}), 201

@api_bp.route('/checklist-templates', methods=['GET'])
@token_required
def get_all_checklist_templates(current_user):
    templates = ChecklistTemplate.query.all()
    output = []
    for t in templates:
        items = []
        for item in t.items:
            items.append({
                'id': item.id,
                'item_description': item.item_description,
                'expected_status': item.expected_status,
                'equipment_id': item.equipment_id
            })
        output.append({
            'id': t.id, 
            'name': t.name, 
            'type': t.type, 
            'description': t.description,
            'items': items
        })
    return jsonify({'checklist_templates': output})

@api_bp.route('/checklist-templates/<int:template_id>', methods=['GET'])
@token_required
def get_checklist_template(current_user, template_id):
    t = ChecklistTemplate.query.get_or_404(template_id)
    items = []
    for item in t.items:
        items.append({
            'id': item.id,
            'item_description': item.item_description,
            'expected_status': item.expected_status,
            'equipment_id': item.equipment_id
        })
    return jsonify({
        'id': t.id, 
        'name': t.name, 
        'type': t.type, 
        'description': t.description,
        'items': items
    })

# PUT and DELETE for templates can be added if time permits, following similar patterns.

# == Checklist Submission and Retrieval ==
@api_bp.route('/checklists', methods=['POST'])
@token_required
def submit_checklist(current_user):
    data = request.get_json()
    if not data or not data.get('checklist_template_id') or not data.get('items'):
        return jsonify({'message': 'Missing checklist_template_id or items'}), 400

    template = ChecklistTemplate.query.get(data['checklist_template_id'])
    if not template:
        return jsonify({'message': 'Checklist template not found'}), 404

    new_checklist = Checklist(
        user_id=current_user.id,
        checklist_template_id=data['checklist_template_id'],
        status=data.get('status', 'completed'), # Default to completed
        notes=data.get('notes')
    )
    db.session.add(new_checklist)

    for item_data in data['items']:
        if not item_data.get('item_description_from_template') or not item_data.get('status'): # item_description could be copied from template item by frontend
            db.session.rollback()
            return jsonify({'message': 'item_description_from_template and status are required for all checklist items'}), 400
        
        equipment_id = item_data.get('equipment_id')
        if equipment_id and not Equipment.query.get(equipment_id):
            db.session.rollback()
            return jsonify({'message': f"Equipment with ID {equipment_id} not found for an item"}), 400

        checklist_item = ChecklistItemInstance(
            # checklist_id will be set by SQLAlchemy relationship append below
            equipment_id=equipment_id,
            item_description_from_template=item_data['item_description_from_template'],
            status=item_data['status'],
            notes=item_data.get('notes')
        )
        new_checklist.items.append(checklist_item)
    
    db.session.commit()
    return jsonify({'message': 'Checklist submitted successfully', 'id': new_checklist.id}), 201

@api_bp.route('/checklists', methods=['GET'])
@token_required
def get_user_checklists(current_user):
    checklists = Checklist.query.filter_by(user_id=current_user.id).order_by(Checklist.completed_at.desc()).all()
    output = []
    for chk in checklists:
        items = []
        for item in chk.items:
            items.append({
                'id': item.id,
                'equipment_id': item.equipment_id,
                'item_description_from_template': item.item_description_from_template,
                'status': item.status,
                'notes': item.notes
            })
        output.append({
            'id': chk.id,
            'user_id': chk.user_id,
            'checklist_template_id': chk.checklist_template_id,
            'template_name': chk.template.name, 
            'completed_at': chk.completed_at.isoformat(),
            'status': chk.status,
            'notes': chk.notes,
            'items': items
        })
    return jsonify({'checklists': output})

@api_bp.route('/checklists/<int:checklist_id>', methods=['GET'])
@token_required
def get_checklist_details(current_user, checklist_id):
    chk = Checklist.query.filter_by(id=checklist_id).first_or_404()
    if chk.user_id != current_user.id: 
        # Potentially allow admin access here too
        return jsonify({'message': 'Not authorized to view this checklist'}), 403

    items = []
    for item in chk.items:
        items.append({
            'id': item.id,
            'equipment_id': item.equipment_id,
            'equipment_name': item.equipment.name if item.equipment else None, 
            'item_description_from_template': item.item_description_from_template,
            'status': item.status,
            'notes': item.notes
        })
    return jsonify({
        'id': chk.id,
        'user_id': chk.user_id,
        'checklist_template_id': chk.checklist_template_id,
        'template_name': chk.template.name,
        'completed_at': chk.completed_at.isoformat(),
        'status': chk.status,
        'notes': chk.notes,
        'items': items
    })

@api_bp.route('/equipment/<int:equipment_id>/history', methods=['GET'])
@token_required
def get_equipment_history(current_user, equipment_id):
    Equipment.query.get_or_404(equipment_id) 
    
    item_instances = ChecklistItemInstance.query.filter_by(equipment_id=equipment_id) \
        .order_by(ChecklistItemInstance.timestamp.desc()).all()
    
    history = []
    for item in item_instances:
        history.append({
            'checklist_id': item.checklist_id,
            'checked_at': item.timestamp.isoformat(),
            'status': item.status,
            'notes': item.notes,
            'description_from_check': item.item_description_from_template,
               'user_id': item.checklist.user_id,
               'equipment_id': item.equipment_id # Added equipment_id
            # 'user_name': item.checklist.user.username 
        })
    return jsonify({'equipment_id': equipment_id, 'history': history})
