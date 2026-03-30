"""
Reports Routes
CSV export for expenses/income and monthly/yearly summary.
"""
import csv
import io
from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Income, Expense
from utils.helpers import success_response, error_response
from sqlalchemy import func, extract

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('/export/expenses', methods=['GET'])
@jwt_required()
def export_expenses_csv():
    """Export all user expenses as a CSV file."""
    user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Amount', 'Category', 'Date', 'Description'])

    for e in expenses:
        writer.writerow([e.id, e.amount, e.category, e.date.isoformat(), e.description])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=expenses.csv'}
    )


@reports_bp.route('/export/income', methods=['GET'])
@jwt_required()
def export_income_csv():
    """Export all user income as a CSV file."""
    user_id = int(get_jwt_identity())
    incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Amount', 'Source', 'Date', 'Description'])

    for i in incomes:
        writer.writerow([i.id, i.amount, i.source, i.date.isoformat(), i.description])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=income.csv'}
    )


@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """
    Monthly/yearly financial summary.
    Query params: year (optional), month (optional).
    """
    user_id = int(get_jwt_identity())
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    # Build income query
    inc_query = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == user_id)
    exp_query = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == user_id)

    if year:
        inc_query = inc_query.filter(extract('year', Income.date) == year)
        exp_query = exp_query.filter(extract('year', Expense.date) == year)
    if month:
        inc_query = inc_query.filter(extract('month', Income.date) == month)
        exp_query = exp_query.filter(extract('month', Expense.date) == month)

    total_income = float(inc_query.scalar())
    total_expenses = float(exp_query.scalar())
    net_savings = total_income - total_expenses

    # Category breakdown
    cat_query = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(Expense.user_id == user_id)

    if year:
        cat_query = cat_query.filter(extract('year', Expense.date) == year)
    if month:
        cat_query = cat_query.filter(extract('month', Expense.date) == month)

    cat_breakdown = cat_query.group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    # Income source breakdown
    src_query = db.session.query(
        Income.source,
        func.sum(Income.amount).label('total')
    ).filter(Income.user_id == user_id)

    if year:
        src_query = src_query.filter(extract('year', Income.date) == year)
    if month:
        src_query = src_query.filter(extract('month', Income.date) == month)

    src_breakdown = src_query.group_by(Income.source).order_by(func.sum(Income.amount).desc()).all()

    return success_response({
        'period': {
            'year': year or 'All',
            'month': month or 'All'
        },
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'net_savings': round(net_savings, 2),
        'savings_percentage': round((net_savings / total_income * 100) if total_income > 0 else 0, 1),
        'expense_categories': [{'category': c[0], 'total': float(c[1])} for c in cat_breakdown],
        'income_sources': [{'source': s[0], 'total': float(s[1])} for s in src_breakdown]
    })
