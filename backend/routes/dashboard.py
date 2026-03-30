"""
Dashboard Routes
Provides aggregate financial stats: totals, savings, monthly trends, category breakdown.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Income, Expense, Budget
from utils.helpers import success_response, error_response
from sqlalchemy import func, extract
from datetime import date, datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get complete dashboard data for the logged-in user."""
    user_id = int(get_jwt_identity())
    today = date.today()

    # --- Totals ---
    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter_by(user_id=user_id).scalar()
    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter_by(user_id=user_id).scalar()
    total_income = float(total_income)
    total_expenses = float(total_expenses)
    net_savings = total_income - total_expenses
    savings_pct = (net_savings / total_income * 100) if total_income > 0 else 0

    # --- Current month totals ---
    month_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == today.month,
        extract('year', Income.date) == today.year
    ).scalar()

    month_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar()

    month_income = float(month_income)
    month_expenses = float(month_expenses)

    # --- Monthly trends (last 6 months) ---
    monthly_trends = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        m_inc = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.user_id == user_id,
            extract('month', Income.date) == m,
            extract('year', Income.date) == y
        ).scalar()

        m_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == m,
            extract('year', Expense.date) == y
        ).scalar()

        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_trends.append({
            'month': f'{month_names[m]} {y}',
            'income': float(m_inc),
            'expenses': float(m_exp),
            'savings': float(m_inc) - float(m_exp)
        })

    # --- Category-wise breakdown (current month) ---
    cat_breakdown = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    categories = [{'category': c[0], 'total': float(c[1])} for c in cat_breakdown]

    # --- Recent transactions (last 10) ---
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).limit(5).all()
    recent_incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).limit(5).all()

    recent = []
    for e in recent_expenses:
        d = e.to_dict()
        d['type'] = 'expense'
        recent.append(d)
    for i in recent_incomes:
        d = i.to_dict()
        d['type'] = 'income'
        recent.append(d)

    recent.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent = recent[:10]

    # --- Budget utilization ---
    budgets = Budget.query.filter_by(user_id=user_id, month=today.month, year=today.year).all()
    budget_status = []
    for b in budgets:
        spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            Expense.category == b.category,
            extract('month', Expense.date) == today.month,
            extract('year', Expense.date) == today.year
        ).scalar()
        spent = float(spent)
        utilization = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0

        budget_status.append({
            'category': b.category,
            'limit': b.limit_amount,
            'spent': spent,
            'remaining': b.limit_amount - spent,
            'utilization': round(utilization, 1),
            'exceeded': spent > b.limit_amount
        })

    return success_response({
        'totals': {
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_savings': round(net_savings, 2),
            'savings_percentage': round(savings_pct, 1)
        },
        'current_month': {
            'income': round(month_income, 2),
            'expenses': round(month_expenses, 2),
            'savings': round(month_income - month_expenses, 2)
        },
        'monthly_trends': monthly_trends,
        'category_breakdown': categories,
        'recent_transactions': recent,
        'budget_status': budget_status
    })
