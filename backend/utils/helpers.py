"""
Utility helpers for validation, formatting, and common operations.
"""
from datetime import datetime
from functools import wraps
from flask import jsonify


def validate_required_fields(data, fields):
    """
    Validate that all required fields exist and are non-empty in the request data.
    Returns (is_valid, error_message).
    """
    if not data:
        return False, 'Request body is required'
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return False, f'Missing required fields: {", ".join(missing)}'
    return True, None


def parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object. Returns None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def format_currency(amount):
    """Format a numeric amount as currency string."""
    try:
        return f'₹{float(amount):,.2f}'
    except (ValueError, TypeError):
        return '₹0.00'


def success_response(data=None, message='Success', status=200):
    """Standard success JSON response."""
    resp = {'status': 'success', 'message': message}
    if data is not None:
        resp['data'] = data
    return jsonify(resp), status


def error_response(message='An error occurred', status=400):
    """Standard error JSON response."""
    return jsonify({'status': 'error', 'message': message}), status
