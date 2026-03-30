"""
Insights Routes
Smart financial insights powered by pandas analysis.
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Income, Expense, Budget
from services.insight_service import generate_insights
from utils.helpers import success_response

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')


@insights_bp.route('', methods=['GET'])
@jwt_required()
def get_insights():
    """Get AI-powered financial insights and suggestions."""
    user_id = int(get_jwt_identity())

    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date).all()
    incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date).all()
    budgets = Budget.query.filter_by(user_id=user_id).all()

    result = generate_insights(expenses, incomes, budgets)
    return success_response(result)
