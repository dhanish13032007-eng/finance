"""
Home Finance Management Application
Entry point — initializes Flask app, extensions, blueprints, and serves templates.
"""
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from config import Config
from models import db

# Extensions (initialized in create_app)
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app():
    """Application factory pattern."""
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from routes.auth import auth_bp
    from routes.income import income_bp
    from routes.expenses import expenses_bp
    from routes.dashboard import dashboard_bp
    from routes.reports import reports_bp
    from routes.prediction import prediction_bp
    from routes.insights import insights_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(insights_bp)

    # --- Budget API (inline for simplicity) ---
    from flask import request, jsonify
    from flask_jwt_extended import jwt_required, get_jwt_identity
    from models import Budget, Expense
    from utils.helpers import success_response, error_response, validate_required_fields
    from datetime import date

    @app.route('/api/budgets', methods=['GET'])
    @jwt_required()
    def get_budgets():
        user_id = int(get_jwt_identity())
        month = request.args.get('month', type=int, default=date.today().month)
        year = request.args.get('year', type=int, default=date.today().year)
        budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
        return success_response([b.to_dict() for b in budgets])

    @app.route('/api/budgets', methods=['POST'])
    @jwt_required()
    def set_budget():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        valid, msg = validate_required_fields(data, ['category', 'limit_amount'])
        if not valid:
            return error_response(msg)

        month = data.get('month', date.today().month)
        year = data.get('year', date.today().year)

        # Upsert: update if exists, create if not
        budget = Budget.query.filter_by(
            user_id=user_id, category=data['category'], month=month, year=year
        ).first()

        if budget:
            budget.limit_amount = float(data['limit_amount'])
        else:
            budget = Budget(
                user_id=user_id,
                category=data['category'],
                limit_amount=float(data['limit_amount']),
                month=month,
                year=year
            )
            db.session.add(budget)

        db.session.commit()
        return success_response(budget.to_dict(), 'Budget saved')

    @app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
    @jwt_required()
    def delete_budget(budget_id):
        user_id = int(get_jwt_identity())
        budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first()
        if not budget:
            return error_response('Budget not found', 404)
        db.session.delete(budget)
        db.session.commit()
        return success_response(message='Budget deleted')

    # --- Template routes ---
    @app.route('/')
    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.route('/income')
    def income_page():
        return render_template('income.html')

    @app.route('/expenses')
    def expenses_page():
        return render_template('expenses.html')

    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
