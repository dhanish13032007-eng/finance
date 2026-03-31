"""
Accounts Routes
Manage user financial accounts (Bank, Wallet, Cash) for net worth tracking.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Account, Income, Expense
from utils.helpers import success_response, error_response, validate_required_fields
from sqlalchemy import func

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/api/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """Get all accounts and their calculated real-time balances."""
    user_id = int(get_jwt_identity())
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    account_list = []
    total_net_worth = 0.0
    
    for acc in accounts:
        # Calculate dynamic balance
        total_in = db.session.query(func.sum(Income.amount)).filter_by(account_id=acc.id).scalar() or 0.0
        total_out = db.session.query(func.sum(Expense.amount)).filter_by(account_id=acc.id).scalar() or 0.0
        
        # Real-time balance = base_balance + incomes - expenses
        current_balance = acc.balance + total_in - total_out
        total_net_worth += current_balance
        
        acc_dict = acc.to_dict()
        acc_dict['current_balance'] = current_balance
        account_list.append(acc_dict)

    return success_response({
        'accounts': account_list,
        'net_worth': total_net_worth
    })

@accounts_bp.route('/api/accounts', methods=['POST'])
@jwt_required()
def create_account():
    """Create a new account."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['name', 'type'])
    if not valid:
        return error_response(msg)

    initial_balance = float(data.get('balance', 0.0))
    
    account = Account(
        user_id=user_id,
        name=data['name'],
        type=data['type'],
        balance=initial_balance
    )
    db.session.add(account)
    db.session.commit()
    
    return success_response(account.to_dict(), 'Account created successfully')

@accounts_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    """Delete an account (and its associated records via CASCADE)."""
    user_id = int(get_jwt_identity())
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return error_response('Account not found', 404)
        
    db.session.delete(account)
    db.session.commit()
    return success_response(message='Account deleted successfully')
