"""
Goals Routes
Manage user savings goals.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Goal
from utils.helpers import success_response, error_response, validate_required_fields
from datetime import datetime

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/api/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """Retrieve all savings goals."""
    user_id = int(get_jwt_identity())
    goals = Goal.query.filter_by(user_id=user_id).all()
    
    goal_list = []
    for g in goals:
        g_dict = g.to_dict()
        g_dict['progress_percent'] = min(100.0, round((g.current_amount / g.target_amount) * 100, 1)) if g.target_amount > 0 else 0
        goal_list.append(g_dict)
        
    return success_response(goal_list)

@goals_bp.route('/api/goals', methods=['POST'])
@jwt_required()
def create_goal():
    """Create a new savings goal."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['name', 'target_amount'])
    if not valid:
        return error_response(msg)

    deadline = None
    if 'deadline' in data and data['deadline']:
        try:
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD")

    goal = Goal(
        user_id=user_id,
        name=data['name'],
        target_amount=float(data['target_amount']),
        current_amount=float(data.get('current_amount', 0.0)),
        deadline=deadline,
        color=data.get('color', '#6C5CE7')
    )
    
    db.session.add(goal)
    db.session.commit()
    return success_response(goal.to_dict(), 'Goal created successfully')

@goals_bp.route('/api/goals/<int:goal_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_goal(goal_id):
    """Update goal progress (add savings to current amount)."""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error_response('Goal not found', 404)
        
    data = request.get_json()
    
    if 'add_amount' in data:
        goal.current_amount += float(data['add_amount'])
    if 'current_amount' in data:
        goal.current_amount = float(data['current_amount'])
    if 'target_amount' in data:
        goal.target_amount = float(data['target_amount'])
        
    db.session.commit()
    
    # Check if achieved
    if goal.current_amount >= goal.target_amount:
        from services.notification_service import check_savings_goal_progress
        check_savings_goal_progress(user_id)
        
    return success_response(goal.to_dict(), 'Goal updated')

@goals_bp.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    """Delete a goal."""
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return error_response('Goal not found', 404)
        
    db.session.delete(goal)
    db.session.commit()
    return success_response(message='Goal deleted successfully')
