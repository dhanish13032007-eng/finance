"""
Income Routes
Full CRUD for income management with per-user data isolation.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Income
from utils.helpers import (
    validate_required_fields, parse_date, success_response, error_response
)
from datetime import date

income_bp = Blueprint('income', __name__, url_prefix='/api/income')


@income_bp.route('', methods=['GET'])
@jwt_required()
def get_all_income():
    """Get all income records for the current user."""
    user_id = int(get_jwt_identity())
    incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).all()
    return success_response([i.to_dict() for i in incomes])


@income_bp.route('', methods=['POST'])
@jwt_required()
def add_income():
    """Add a new income record."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    valid, msg = validate_required_fields(data, ['amount', 'source'])
    if not valid:
        return error_response(msg)

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return error_response('Amount must be positive')
    except (ValueError, TypeError):
        return error_response('Invalid amount')

    income_date = parse_date(data.get('date')) or date.today()

    income = Income(
        user_id=user_id,
        amount=amount,
        source=data['source'].strip(),
        date=income_date,
        description=data.get('description', '').strip()
    )
    
    if data.get('account_id'):
        income.account_id = data['account_id']
        
    db.session.add(income)
    db.session.commit()

    return success_response(income.to_dict(), 'Income added successfully', 201)


@income_bp.route('/<int:income_id>', methods=['PUT'])
@jwt_required()
def update_income(income_id):
    """Update an existing income record."""
    user_id = int(get_jwt_identity())
    income = Income.query.filter_by(id=income_id, user_id=user_id).first()

    if not income:
        return error_response('Income record not found', 404)

    data = request.get_json()
    if not data:
        return error_response('Request body is required')

    if 'amount' in data:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return error_response('Amount must be positive')
            income.amount = amount
        except (ValueError, TypeError):
            return error_response('Invalid amount')

    if 'source' in data and data['source'].strip():
        income.source = data['source'].strip()

    if 'date' in data:
        parsed = parse_date(data['date'])
        if parsed:
            income.date = parsed

    if 'description' in data:
        income.description = data['description'].strip()

    db.session.commit()
    return success_response(income.to_dict(), 'Income updated successfully')


@income_bp.route('/<int:income_id>', methods=['DELETE'])
@jwt_required()
def delete_income(income_id):
    """Delete an income record."""
    user_id = int(get_jwt_identity())
    income = Income.query.filter_by(id=income_id, user_id=user_id).first()

    if not income:
        return error_response('Income record not found', 404)

    db.session.delete(income)
    db.session.commit()
    return success_response(message='Income deleted successfully')
