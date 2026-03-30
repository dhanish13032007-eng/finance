"""
What-If Simulator Route
Calculates projected savings if an expense category is reduced.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Income, Expense
from utils.helpers import success_response, error_response
from sqlalchemy import func, extract
from datetime import date

whatif_bp = Blueprint('whatif', __name__, url_prefix='/api/whatif')

@whatif_bp.route('', methods=['POST'])
@jwt_required()
def simulate_whatif():
    """
    Simulate reducing a specific expense category.
    Accepts: { "category": str, "reduce_by_percent": float }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'category' not in data or 'reduce_by_percent' not in data:
        return error_response('Missing category or reduce_by_percent')
        
    category = data['category']
    try:
        reduce_pct = float(data['reduce_by_percent'])
    except ValueError:
        return error_response('Invalid reduce_by_percent')

    today = date.today()
    
    # Get current month totals
    month_inc = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == today.month,
        extract('year', Income.date) == today.year
    ).scalar()
    
    month_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar()
    
    cat_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar()
    
    month_inc = float(month_inc)
    month_exp = float(month_exp)
    cat_exp = float(cat_exp)
    
    current_savings = month_inc - month_exp
    current_rate = (current_savings / month_inc * 100) if month_inc > 0 else 0
    
    reduction_amount = cat_exp * (reduce_pct / 100.0)
    new_exp = month_exp - reduction_amount
    new_savings = month_inc - new_exp
    new_rate = (new_savings / month_inc * 100) if month_inc > 0 else 0
    
    return success_response({
        'current_savings': current_savings,
        'current_savings_rate': round(current_rate, 1),
        'category_current_spend': cat_exp,
        'reduction_amount': reduction_amount,
        'projected_savings': new_savings,
        'projected_savings_rate': round(new_rate, 1),
        'difference': reduction_amount
    })
