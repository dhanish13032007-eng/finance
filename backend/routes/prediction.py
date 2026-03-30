"""
Prediction Routes
ML-powered expense and savings predictions.
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Income, Expense
from services.ml_service import predict_expenses, predict_savings
from utils.helpers import success_response, error_response

prediction_bp = Blueprint('prediction', __name__, url_prefix='/api/prediction')


@prediction_bp.route('', methods=['GET'])
@jwt_required()
def get_prediction():
    """Get ML-powered predictions for expenses and savings."""
    user_id = int(get_jwt_identity())

    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date).all()
    incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date).all()

    expense_prediction = predict_expenses(expenses)
    savings_prediction = predict_savings(incomes, expenses)

    return success_response({
        'expense_prediction': expense_prediction,
        'savings_prediction': savings_prediction
    })
