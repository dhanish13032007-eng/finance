"""
Insight Service
Analyzes spending patterns using pandas to generate smart financial insights.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from collections import defaultdict


def generate_insights(expenses_list, incomes_list, budgets_list):
    """
    Analyze user's financial data and generate actionable insights.

    Args:
        expenses_list: List of Expense model objects.
        incomes_list: List of Income model objects.
        budgets_list: List of Budget model objects.

    Returns:
        dict with insights, alerts, and suggestions.
    """
    insights = []
    alerts = []
    suggestions = []

    if not expenses_list:
        return {
            'insights': [{'type': 'info', 'title': 'No Data Yet', 'message': 'Start adding expenses to get personalized insights.'}],
            'alerts': [],
            'suggestions': ['Add your first expense to begin tracking your finances.']
        }

    # --- Build DataFrames ---
    exp_data = [{
        'amount': e.amount,
        'category': e.category,
        'date': e.date,
        'description': e.description
    } for e in expenses_list]
    df_exp = pd.DataFrame(exp_data)
    df_exp['date'] = pd.to_datetime(df_exp['date'])
    df_exp['month'] = df_exp['date'].dt.to_period('M')
    df_exp['month_str'] = df_exp['date'].dt.strftime('%Y-%m')

    # --- 1. High spending categories ---
    cat_totals = df_exp.groupby('category')['amount'].sum().sort_values(ascending=False)
    total_exp = cat_totals.sum()

    if total_exp > 0:
        top_cat = cat_totals.index[0]
        top_pct = (cat_totals.iloc[0] / total_exp) * 100
        insights.append({
            'type': 'spending',
            'title': 'Highest Spending Category',
            'message': f'"{top_cat}" accounts for {top_pct:.1f}% of your total expenses (₹{cat_totals.iloc[0]:,.2f}).',
            'icon': '💸'
        })

        if top_pct > 40:
            suggestions.append(f'Consider reducing spending on "{top_cat}" — it\'s over 40% of your total expenses.')

    # --- 2. Monthly trend analysis ---
    monthly_totals = df_exp.groupby('month_str')['amount'].sum().sort_index()

    if len(monthly_totals) >= 2:
        last_month = monthly_totals.iloc[-1]
        prev_month = monthly_totals.iloc[-2]
        change_pct = ((last_month - prev_month) / prev_month) * 100 if prev_month > 0 else 0

        if change_pct > 20:
            insights.append({
                'type': 'trend',
                'title': 'Spending Spike Detected',
                'message': f'Your spending increased by {change_pct:.1f}% compared to last month.',
                'icon': '📈'
            })
            alerts.append({
                'type': 'warning',
                'title': 'Spending Increase Alert',
                'message': f'Expenses rose from ₹{prev_month:,.2f} to ₹{last_month:,.2f} ({change_pct:+.1f}%).'
            })
        elif change_pct < -10:
            insights.append({
                'type': 'trend',
                'title': 'Spending Decreased',
                'message': f'Great! Your spending decreased by {abs(change_pct):.1f}% compared to last month.',
                'icon': '📉'
            })
        else:
            insights.append({
                'type': 'trend',
                'title': 'Stable Spending',
                'message': f'Your spending is relatively stable (changed by {change_pct:+.1f}%).',
                'icon': '➡️'
            })

    # --- 3. Category trend (which categories are increasing) ---
    if len(monthly_totals) >= 2:
        recent_months = sorted(df_exp['month_str'].unique())[-2:]
        if len(recent_months) == 2:
            prev_m = df_exp[df_exp['month_str'] == recent_months[0]].groupby('category')['amount'].sum()
            curr_m = df_exp[df_exp['month_str'] == recent_months[1]].groupby('category')['amount'].sum()

            for cat in curr_m.index:
                curr_val = curr_m.get(cat, 0)
                prev_val = prev_m.get(cat, 0)
                if prev_val > 0 and ((curr_val - prev_val) / prev_val) > 0.3:
                    suggestions.append(
                        f'"{cat}" spending increased by {((curr_val - prev_val) / prev_val) * 100:.0f}% this month. Review recent purchases.'
                    )

    # --- 4. Budget utilization alerts ---
    today = date.today()
    for budget in budgets_list:
        if budget.month == today.month and budget.year == today.year:
            cat_spent = sum(
                e.amount for e in expenses_list
                if e.category == budget.category
                and e.date.month == today.month
                and e.date.year == today.year
            )
            utilization = (cat_spent / budget.limit_amount * 100) if budget.limit_amount > 0 else 0

            if utilization >= 100:
                alerts.append({
                    'type': 'danger',
                    'title': f'Budget Exceeded: {budget.category}',
                    'message': f'You\'ve spent ₹{cat_spent:,.2f} of your ₹{budget.limit_amount:,.2f} budget ({utilization:.0f}%).'
                })
            elif utilization >= 80:
                alerts.append({
                    'type': 'warning',
                    'title': f'Budget Warning: {budget.category}',
                    'message': f'You\'ve used {utilization:.0f}% of your {budget.category} budget (₹{cat_spent:,.2f} / ₹{budget.limit_amount:,.2f}).'
                })

    # --- 5. Savings insight ---
    if incomes_list:
        total_income = sum(i.amount for i in incomes_list)
        if total_income > 0:
            savings_rate = ((total_income - total_exp) / total_income) * 100
            insights.append({
                'type': 'savings',
                'title': 'Savings Rate',
                'message': f'Your overall savings rate is {savings_rate:.1f}%.',
                'icon': '💰'
            })

            if savings_rate < 10:
                suggestions.append('Your savings rate is below 10%. Try to cut discretionary spending.')
            elif savings_rate > 30:
                suggestions.append('Excellent savings rate! Consider investing your surplus.')

    # --- 6. Average daily spend ---
    if len(df_exp) > 0:
        date_range = (df_exp['date'].max() - df_exp['date'].min()).days + 1
        if date_range > 0:
            avg_daily = total_exp / date_range
            insights.append({
                'type': 'daily',
                'title': 'Average Daily Spend',
                'message': f'You spend an average of ₹{avg_daily:,.2f} per day.',
                'icon': '📅'
            })

    return {
        'insights': insights,
        'alerts': alerts,
        'suggestions': suggestions,
        'summary': {
            'total_expenses': round(total_exp, 2),
            'num_categories': len(cat_totals),
            'num_transactions': len(df_exp),
            'top_category': cat_totals.index[0] if len(cat_totals) > 0 else None
        }
    }
