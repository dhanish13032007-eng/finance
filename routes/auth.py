"""
Authentication Routes
Handles registration, login, profile management, and password change.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from models import db, User
from utils.helpers import validate_required_fields, success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _get_bcrypt():
    """Return the shared Bcrypt instance from app.py."""
    from app import bcrypt
    return bcrypt


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['name', 'email', 'password'])
    if not valid:
        return error_response(msg)

    # Validate email format
    email = data['email'].strip().lower()
    if '@' not in email or '.' not in email:
        return error_response('Invalid email format')

    # Check password length
    if len(data['password']) < 6:
        return error_response('Password must be at least 6 characters')

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return error_response('Email already registered', 409)

    # Hash password and create user
    bcrypt = _get_bcrypt()
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        name=data['name'].strip(),
        email=email,
        password=hashed_pw
    )
    db.session.add(user)
    db.session.commit()

    return success_response(user.to_dict(), 'Registration successful', 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    valid, msg = validate_required_fields(data, ['email', 'password'])
    if not valid:
        return error_response(msg)

    email = data['email'].strip().lower()
    user = User.query.filter_by(email=email).first()

    bcrypt = _get_bcrypt()
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return error_response('Invalid email or password', 401)

    access_token = create_access_token(identity=str(user.id))

    return success_response({
        'token': access_token,
        'user': user.to_dict()
    }, 'Login successful')


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get the current user's profile."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return error_response('User not found', 404)
    return success_response(user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user's name and/or email."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return error_response('User not found', 404)

    data = request.get_json()
    if not data:
        return error_response('Request body is required')

    if 'name' in data and data['name'].strip():
        user.name = data['name'].strip()

    if 'email' in data and data['email'].strip():
        new_email = data['email'].strip().lower()
        if new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                return error_response('Email already in use', 409)
            user.email = new_email

    db.session.commit()
    return success_response(user.to_dict(), 'Profile updated')


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change password (requires old password verification)."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return error_response('User not found', 404)

    data = request.get_json()
    valid, msg = validate_required_fields(data, ['old_password', 'new_password'])
    if not valid:
        return error_response(msg)

    bcrypt = _get_bcrypt()
    if not bcrypt.check_password_hash(user.password, data['old_password']):
        return error_response('Current password is incorrect', 401)

    if len(data['new_password']) < 6:
        return error_response('New password must be at least 6 characters')

    user.password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
    db.session.commit()

    return success_response(message='Password changed successfully')
