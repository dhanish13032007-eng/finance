"""
Notification Service
Trigger automatic real-time alerts.
Runs when transactions are added to check budget thresholds, recurring billing, etc.
"""
from models import db, Notification, Budget, Expense, Goal
from datetime import date
from sqlalchemy import func

def create_notification(user_id, title, message, alert_type='info'):
    """Create a persistent notification."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=alert_type # info, warning, danger, success
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def alert_if_budget_exceeded(user_id, category):
    """Check budget limits for a category and create a notification if nearing/exceeded."""
    today = date.today()
    budget = Budget.query.filter_by(
        user_id=user_id, category=category, month=today.month, year=today.year
    ).first()
    
    if not budget:
        return None

    spent = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        func.extract('month', Expense.date) == today.month,
        func.extract('year', Expense.date) == today.year
    ).scalar() or 0.0

    percent = (spent / budget.limit_amount) * 100 if budget.limit_amount > 0 else 0

    if percent >= 100:
        # Check if we already notified today
        exists = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == f"Budget Exceeded: {category}"
        ).first()
        if not exists:
            create_notification(
                user_id, 
                f"Budget Exceeded: {category}", 
                f"You have spent ₹{spent:,.2f}, exceeding your ₹{budget.limit_amount:,.2f} limit.",
                'danger'
            )
    elif percent >= 80:
         exists = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == f"Budget Warning: {category}"
         ).first()
         if not exists:
            create_notification(
                user_id, 
                f"Budget Warning: {category}", 
                f"You are at {percent:.1f}% of your budget for {category}.",
                'warning'
            )

def alert_unusual_spending(user_id, amount, category):
    """Simple anomaly detection: Warn if a single expense is massive compared to usual."""
    # Find average expense for this category
    avg = db.session.query(func.avg(Expense.amount)).filter_by(user_id=user_id).scalar() or 0.0
    
    # If the transaction is >3x the average (and > 2000), anomaly
    if avg > 0 and amount > (avg * 3) and amount > 2000:
        create_notification(
            user_id,
            "Unusual Spending Spike Detected",
            f"An unusually large expense of ₹{amount:,.2f} was recorded under {category}. Please verify.",
            'warning'
        )

def check_savings_goal_progress(user_id):
    """Check goals - celebrate if achieved!"""
    goals = Goal.query.filter_by(user_id=user_id).all()
    for g in goals:
        if g.current_amount >= g.target_amount:
            exists = Notification.query.filter_by(user_id=user_id, title=f"Goal Reached: {g.name}").first()
            if not exists:
                create_notification(
                    user_id,
                    f"Goal Reached: {g.name}",
                    f"Congratulations! You reached your savings goal of ₹{g.target_amount:,.2f}.",
                    'success'
                )

def on_expense_added(expense):
    """Hook to call when an expense is added."""
    user_id = expense.user_id
    alert_unusual_spending(user_id, expense.amount, expense.category)
    alert_if_budget_exceeded(user_id, expense.category)
    check_savings_goal_progress(user_id)
