"""
What-If Simulator Route — v2.0
Calculates projected savings impact if an expense category is reduced.
Now includes:
  - Yearly savings impact
  - Savings rate change
  - Human-readable narrative explanation
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
    Returns monthly + yearly savings impact with narrative.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or 'category' not in data or 'reduce_by_percent' not in data:
        return error_response('Missing category or reduce_by_percent')

    category = data['category']
    try:
        reduce_pct = float(data['reduce_by_percent'])
        if not (0 <= reduce_pct <= 100):
            return error_response('reduce_by_percent must be between 0 and 100')
    except (ValueError, TypeError):
        return error_response('Invalid reduce_by_percent')

    today = date.today()

    # Current month totals
    month_inc = float(db.session.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == today.month,
        extract('year', Income.date) == today.year
    ).scalar())

    month_exp = float(db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar())

    cat_exp = float(db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar())

    # Current state
    current_savings = month_inc - month_exp
    current_rate = (current_savings / month_inc * 100) if month_inc > 0 else 0

    # Simulated state
    reduction_amount = cat_exp * (reduce_pct / 100.0)
    new_exp = month_exp - reduction_amount
    new_savings = month_inc - new_exp
    new_rate = (new_savings / month_inc * 100) if month_inc > 0 else 0

    # Yearly projections
    current_yearly = current_savings * 12
    projected_yearly = new_savings * 12
    yearly_gain = projected_yearly - current_yearly

    # Savings rate improvement
    rate_improvement = new_rate - current_rate

    # Human-readable narrative
    if reduce_pct == 0:
        narrative = f'No change. Your current monthly savings is ₹{current_savings:,.0f}.'
    elif cat_exp == 0:
        narrative = f'No {category} spending this month to reduce.'
    else:
        narrative = (
            f'By cutting {category} by {reduce_pct:.0f}%, you save ₹{reduction_amount:,.0f} more per month. '
            f'That\'s ₹{yearly_gain:,.0f} extra per year — '
        )
        if yearly_gain >= 100000:
            narrative += f'enough to build a strong emergency fund.'
        elif yearly_gain >= 50000:
            narrative += f'a solid boost to your annual savings.'
        elif yearly_gain >= 10000:
            narrative += f'a meaningful improvement to your finances.'
        else:
            narrative += f'every rupee counts!'

    return success_response({
        # Current
        'current_savings': round(current_savings, 2),
        'current_savings_rate': round(current_rate, 1),
        'current_yearly_savings': round(current_yearly, 2),
        'category_current_spend': round(cat_exp, 2),

        # Simulated
        'reduction_amount': round(reduction_amount, 2),
        'projected_savings': round(new_savings, 2),
        'projected_savings_rate': round(new_rate, 1),
        'projected_yearly_savings': round(projected_yearly, 2),

        # Impact
        'difference': round(reduction_amount, 2),
        'yearly_gain': round(yearly_gain, 2),
        'rate_improvement': round(rate_improvement, 1),

        # Narrative
        'narrative': narrative
    })
