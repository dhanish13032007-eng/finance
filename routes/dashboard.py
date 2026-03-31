"""
Dashboard Routes — v2.0
Provides complete financial intelligence payload:
  - Totals, current/previous month stats
  - Monthly trends (6 months)
  - Category breakdown
  - Budget utilization + Smart Budget (burn rate, exhaustion date, status)
  - Top Issue highlight
  - Spending Behavior signals
  - Recent transactions
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Income, Expense, Budget, Account, Notification, Goal
from utils.helpers import success_response, error_response
from sqlalchemy import func, extract
from datetime import date, timedelta
import calendar

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


def _days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get complete intelligent dashboard payload."""
    user_id = int(get_jwt_identity())
    today = date.today()
    days_in_month = _days_in_month(today.year, today.month)
    days_passed = today.day
    days_remaining = days_in_month - days_passed

    # ── All-time Totals ──
    total_income = float(db.session.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter_by(user_id=user_id).scalar())

    total_expenses = float(db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter_by(user_id=user_id).scalar())

    base_assets = float(db.session.query(
        func.coalesce(func.sum(Account.balance), 0)
    ).filter_by(user_id=user_id).scalar())

    net_savings = total_income - total_expenses
    net_worth = base_assets + net_savings
    savings_pct = (net_savings / total_income * 100) if total_income > 0 else 0
    
    unread_notifications = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    active_goals = Goal.query.filter_by(user_id=user_id).count()

    # ── Current Month ──
    month_income = float(db.session.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == today.month,
        extract('year', Income.date) == today.year
    ).scalar())

    month_expenses = float(db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).scalar())

    # Daily burn rate for current month
    daily_burn = month_expenses / days_passed if days_passed > 0 else 0
    projected_month_spend = month_expenses + daily_burn * days_remaining
    projected_month_savings = month_income - projected_month_spend

    # ── Previous Month ──
    prev_month_val = today.month - 1
    prev_year = today.year
    if prev_month_val == 0:
        prev_month_val = 12
        prev_year -= 1

    prev_month_income = float(db.session.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == prev_month_val,
        extract('year', Income.date) == prev_year
    ).scalar())

    prev_month_expenses = float(db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == prev_month_val,
        extract('year', Expense.date) == prev_year
    ).scalar())

    # ── Monthly Trends (6 months) ──
    monthly_trends = []
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        m_inc = float(db.session.query(
            func.coalesce(func.sum(Income.amount), 0)
        ).filter(
            Income.user_id == user_id,
            extract('month', Income.date) == m,
            extract('year', Income.date) == y
        ).scalar())

        m_exp = float(db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == m,
            extract('year', Expense.date) == y
        ).scalar())

        monthly_trends.append({
            'month': f'{month_names[m]} {y}',
            'income': m_inc,
            'expenses': m_exp,
            'savings': m_inc - m_exp
        })

    # ── Category Breakdown (current month) ──
    cat_breakdown = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == today.month,
        extract('year', Expense.date) == today.year
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    categories = [{'category': c[0], 'total': round(float(c[1]), 2)} for c in cat_breakdown]

    # ── Top Issue ──
    top_issue = None
    if categories and month_expenses > 0:
        worst = categories[0]
        worst_pct = (worst['total'] / month_expenses * 100)
        if worst_pct > 50:
            reason = f'consuming {worst_pct:.0f}% of all spending'
        elif worst_pct > 35:
            reason = f'dominating at {worst_pct:.0f}% of monthly spend'
        else:
            reason = f'your heaviest category at ₹{worst["total"]:,.0f}'
        top_issue = {
            'category': worst['category'],
            'amount': worst['total'],
            'pct_of_spending': round(worst_pct, 1),
            'reason': reason,
            'suggestion': f'Reducing {worst["category"]} by 20% saves ₹{worst["total"] * 0.2:,.0f} this month.'
        }

    # ── Smart Budget Status ──
    budgets = Budget.query.filter_by(user_id=user_id, month=today.month, year=today.year).all()
    budget_status = []
    smart_budget = []

    for b in budgets:
        spent = float(db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.user_id == user_id,
            Expense.category == b.category,
            extract('month', Expense.date) == today.month,
            extract('year', Expense.date) == today.year
        ).scalar())

        limit = float(b.limit_amount)
        utilization = (spent / limit * 100) if limit > 0 else 0
        remaining = limit - spent
        cat_daily_rate = spent / days_passed if days_passed > 0 else 0
        projected = spent + cat_daily_rate * days_remaining
        will_overshoot = projected > limit

        # Exhaustion date
        if cat_daily_rate > 0 and remaining > 0:
            days_to_exhaust = remaining / cat_daily_rate
            exhaust_date = today + timedelta(days=int(days_to_exhaust))
            exhaust_str = exhaust_date.strftime('%b %d') if days_to_exhaust <= days_remaining else 'Safe'
        else:
            days_to_exhaust = None
            exhaust_str = 'Safe' if remaining > 0 else 'Exceeded'

        # Status
        time_pct = (days_passed / days_in_month * 100) if days_in_month > 0 else 0
        if utilization >= 100:
            status = 'Danger'
        elif utilization >= 80 or (utilization > time_pct + 15):
            status = 'Warning'
        else:
            status = 'Safe'

        # Speed label
        if utilization > 0 and time_pct > 0:
            ratio = utilization / time_pct
            speed = 'Very Fast' if ratio >= 1.5 else 'Fast' if ratio >= 1.15 else 'Normal' if ratio >= 0.85 else 'Slow'
        else:
            speed = 'No data'

        budget_status.append({
            'category': b.category,
            'limit': limit,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'utilization': round(utilization, 1),
            'exceeded': spent > limit
        })

        smart_budget.append({
            'category': b.category,
            'limit': limit,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'utilization': round(utilization, 1),
            'daily_rate': round(cat_daily_rate, 2),
            'projected_total': round(projected, 2),
            'will_overshoot': will_overshoot,
            'exhaust_date': exhaust_str,
            'days_to_exhaust': round(days_to_exhaust, 1) if days_to_exhaust and days_to_exhaust <= days_remaining else None,
            'status': status,
            'speed_label': speed,
            'exceeded': spent > limit
        })

    # ── Behavior Signals (lightweight, from DB) ──
    behavior = {
        'daily_burn': round(daily_burn, 2),
        'projected_month_spend': round(projected_month_spend, 2),
        'projected_month_savings': round(projected_month_savings, 2),
        'days_remaining': days_remaining,
        'on_track': projected_month_spend <= month_income if month_income > 0 else True
    }

    # ── Recent Transactions ──
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).limit(5).all()
    recent_incomes = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).limit(5).all()

    recent = []
    for e in recent_expenses:
        d = e.to_dict()
        d['type'] = 'expense'
        recent.append(d)
    for i_rec in recent_incomes:
        d = i_rec.to_dict()
        d['type'] = 'income'
        recent.append(d)
    recent.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent = recent[:10]

    return success_response({
        'totals': {
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'net_savings': round(net_savings, 2),
            'net_worth': round(net_worth, 2),
            'savings_percentage': round(savings_pct, 1),
            'unread_notifications': unread_notifications,
            'active_goals': active_goals
        },
        'current_month': {
            'income': round(month_income, 2),
            'expenses': round(month_expenses, 2),
            'savings': round(month_income - month_expenses, 2),
            'prev_income': round(prev_month_income, 2),
            'prev_expenses': round(prev_month_expenses, 2),
            'prev_savings': round(prev_month_income - prev_month_expenses, 2),
            'daily_burn': round(daily_burn, 2),
            'projected_spend': round(projected_month_spend, 2),
            'projected_savings': round(projected_month_savings, 2),
            'days_remaining': days_remaining
        },
        'monthly_trends': monthly_trends,
        'category_breakdown': categories,
        'top_issue': top_issue,
        'budget_status': budget_status,
        'smart_budget': smart_budget,
        'behavior': behavior,
        'recent_transactions': recent
    })
