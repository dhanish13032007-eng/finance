"""
ML Prediction Service
Uses scikit-learn Linear Regression to predict future expenses and savings.
"""
import numpy as np
from datetime import date, timedelta
from sklearn.linear_model import LinearRegression


def predict_expenses(expenses_list):
    """
    Train a Linear Regression model on historical monthly expense totals
    and predict the next month's expenses.

    Args:
        expenses_list: List of Expense model objects for a user.

    Returns:
        dict with prediction results or error message.
    """
    if not expenses_list:
        return {
            'predicted_next_month_expense': 0,
            'trend': 'neutral',
            'confidence': 0,
            'monthly_data': [],
            'message': 'Not enough data for prediction. Add more expense records.'
        }

    # Aggregate expenses by month
    monthly = {}
    for exp in expenses_list:
        key = (exp.date.year, exp.date.month)
        monthly[key] = monthly.get(key, 0) + exp.amount

    if len(monthly) < 2:
        total = sum(monthly.values())
        return {
            'predicted_next_month_expense': round(total / len(monthly), 2),
            'trend': 'neutral',
            'confidence': 0,
            'monthly_data': [{'month': f'{k[0]}-{k[1]:02d}', 'total': round(v, 2)} for k, v in sorted(monthly.items())],
            'message': 'Need at least 2 months of data for trend prediction. Showing average.'
        }

    # Sort by date and prepare features
    sorted_months = sorted(monthly.keys())
    X = np.array(range(len(sorted_months))).reshape(-1, 1)
    y = np.array([monthly[m] for m in sorted_months])

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next month
    next_idx = np.array([[len(sorted_months)]])
    predicted = float(model.predict(next_idx)[0])
    predicted = max(predicted, 0)  # Expenses can't be negative

    # Determine trend
    slope = float(model.coef_[0])
    if slope > 50:
        trend = 'increasing'
    elif slope < -50:
        trend = 'decreasing'
    else:
        trend = 'stable'

    # R² score as confidence
    score = model.score(X, y)
    confidence = round(max(score * 100, 0), 1)

    monthly_data = [
        {'month': f'{k[0]}-{k[1]:02d}', 'total': round(monthly[k], 2)}
        for k in sorted_months
    ]

    return {
        'predicted_next_month_expense': round(predicted, 2),
        'trend': trend,
        'confidence': confidence,
        'slope': round(slope, 2),
        'monthly_data': monthly_data,
        'message': f'Based on {len(sorted_months)} months of data.'
    }


def predict_savings(incomes_list, expenses_list):
    """
    Predict next month's savings based on income and expense trends.

    Args:
        incomes_list: List of Income model objects.
        expenses_list: List of Expense model objects.

    Returns:
        dict with savings prediction.
    """
    # Aggregate monthly income
    monthly_income = {}
    for inc in incomes_list:
        key = (inc.date.year, inc.date.month)
        monthly_income[key] = monthly_income.get(key, 0) + inc.amount

    # Aggregate monthly expenses
    monthly_expense = {}
    for exp in expenses_list:
        key = (exp.date.year, exp.date.month)
        monthly_expense[key] = monthly_expense.get(key, 0) + exp.amount

    # Get all months present in either
    all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))

    if len(all_months) < 2:
        return {
            'predicted_next_month_savings': 0,
            'trend': 'neutral',
            'message': 'Need at least 2 months of data for savings prediction.'
        }

    # Calculate monthly savings
    monthly_savings = {}
    for m in all_months:
        inc = monthly_income.get(m, 0)
        exp = monthly_expense.get(m, 0)
        monthly_savings[m] = inc - exp

    X = np.array(range(len(all_months))).reshape(-1, 1)
    y = np.array([monthly_savings[m] for m in all_months])

    model = LinearRegression()
    model.fit(X, y)

    next_idx = np.array([[len(all_months)]])
    predicted = float(model.predict(next_idx)[0])

    slope = float(model.coef_[0])
    if slope > 50:
        trend = 'improving'
    elif slope < -50:
        trend = 'declining'
    else:
        trend = 'stable'

    return {
        'predicted_next_month_savings': round(predicted, 2),
        'trend': trend,
        'confidence': round(max(model.score(X, y) * 100, 0), 1),
        'message': f'Based on {len(all_months)} months of data.'
    }
