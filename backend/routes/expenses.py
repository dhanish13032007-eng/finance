"""
Expense Routes
Full CRUD with advanced filtering (date range, category, amount range, keyword).
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Expense
from utils.helpers import (
    validate_required_fields, parse_date, success_response, error_response
)
from datetime import date

expenses_bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')


@expenses_bp.route('', methods=['GET'])
@jwt_required()
def get_all_expenses():
    """
    Get expenses with optional filters:
      - start_date, end_date  (YYYY-MM-DD)
      - category
      - min_amount, max_amount
      - keyword (searches description)
    """
    user_id = int(get_jwt_identity())
    query = Expense.query.filter_by(user_id=user_id)

    # Date range filter
    start_date = parse_date(request.args.get('start_date'))
    end_date = parse_date(request.args.get('end_date'))
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    # Category filter
    category = request.args.get('category')
    if category:
        query = query.filter(Expense.category == category)

    # Amount range filter
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    if min_amount:
        try:
            query = query.filter(Expense.amount >= float(min_amount))
        except ValueError:
            pass
    if max_amount:
        try:
            query = query.filter(Expense.amount <= float(max_amount))
        except ValueError:
            pass

    # Keyword search in description
    keyword = request.args.get('keyword')
    if keyword:
        query = query.filter(Expense.description.ilike(f'%{keyword}%'))

    expenses = query.order_by(Expense.date.desc()).all()
    return success_response([e.to_dict() for e in expenses])


@expenses_bp.route('/categories', methods=['GET'])
def get_categories():
    """Return the list of predefined expense categories."""
    return success_response(Expense.CATEGORIES)


@expenses_bp.route('', methods=['POST'])
@jwt_required()
def add_expense():
    """Add a new expense record."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    valid, msg = validate_required_fields(data, ['amount', 'category'])
    if not valid:
        return error_response(msg)

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return error_response('Amount must be positive')
    except (ValueError, TypeError):
        return error_response('Invalid amount')

    category = data['category'].strip()
    if category not in Expense.CATEGORIES:
        return error_response(f'Invalid category. Valid: {", ".join(Expense.CATEGORIES)}')

    expense_date = parse_date(data.get('date')) or date.today()

    expense = Expense(
        user_id=user_id,
        amount=amount,
        category=category,
        date=expense_date,
        description=data.get('description', '').strip()
    )
    db.session.add(expense)
    db.session.commit()

    return success_response(expense.to_dict(), 'Expense added successfully', 201)


@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """Update an existing expense record."""
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()

    if not expense:
        return error_response('Expense record not found', 404)

    data = request.get_json()
    if not data:
        return error_response('Request body is required')

    if 'amount' in data:
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return error_response('Amount must be positive')
            expense.amount = amount
        except (ValueError, TypeError):
            return error_response('Invalid amount')

    if 'category' in data and data['category'].strip():
        cat = data['category'].strip()
        if cat not in Expense.CATEGORIES:
            return error_response(f'Invalid category')
        expense.category = cat

    if 'date' in data:
        parsed = parse_date(data['date'])
        if parsed:
            expense.date = parsed

    if 'description' in data:
        expense.description = data['description'].strip()

    db.session.commit()
    return success_response(expense.to_dict(), 'Expense updated successfully')


@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense record."""
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()

    if not expense:
        return error_response('Expense record not found', 404)

    db.session.delete(expense)
    db.session.commit()
    return success_response(message='Expense deleted successfully')
