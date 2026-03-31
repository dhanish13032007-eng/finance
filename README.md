# Home Finance Management System

A comprehensive Flask-based web application for managing personal finances, tracking expenses and income, creating budgets, and generating financial insights with ML-powered predictions.

## 🎯 Features

### Core Functionality
- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Expense Tracking**: Log and categorize daily expenses with OCR receipt scanning
- **Income Management**: Track and manage multiple income sources
- **Dashboard**: Real-time overview of financial status and trends
- **Budget Management**: Set and monitor budget goals
- **Financial Insights**: AI-powered analysis of spending patterns
- **Predictions**: Machine learning-based expense and savings forecasting
- **Reports**: Generate detailed financial reports and analytics
- **Notifications**: Get alerts for budget overruns and financial milestones

### Advanced Features
- **OCR Receipt Scanning**: Upload receipts and automatically extract expense data
- **SMS Parsing**: Extract transaction details from SMS alerts
- **What-If Analysis**: Model different financial scenarios
- **Account Management**: Multi-account support with account linking
- **Data Categorization**: Automatic transaction categorization
- **File Upload**: Support for bulk expense uploads

## 🏗️ Project Structure

```
finance/
├── app.py                          # Main Flask application entry point
├── config.py                       # Configuration settings
├── models.py                       # Database models (User, Expense, Income, etc.)
├── migrate_db.py                   # Database migration utilities
├── schema.sql                      # Database schema definition
├── requirements.txt                # Python dependencies
│
├── routes/                         # API endpoints
│   ├── auth.py                     # Authentication routes
│   ├── dashboard.py                # Dashboard data endpoints
│   ├── expenses.py                 # Expense management routes
│   ├── income.py                   # Income management routes
│   ├── accounts.py                 # Account management
│   ├── insights.py                 # Financial insights
│   ├── prediction.py               # ML predictions
│   ├── reports.py                  # Report generation
│   ├── goals.py                    # Budget goals management
│   ├── notifications.py            # Notification endpoints
│   ├── upload.py                   # File upload handling
│   └── whatif.py                   # What-if scenario analysis
│
├── services/                       # Business logic
│   ├── ml_service.py               # Machine learning models
│   ├── insight_service.py          # Insight generation
│   ├── categorization_service.py   # Expense categorization
│   ├── ocr_service.py              # Receipt OCR processing
│   ├── sms_parser.py               # SMS message parsing
│   └── notification_service.py     # Notification handling
│
├── utils/                          # Utility functions
│   └── helpers.py                  # Helper functions
│
├── static/                         # Frontend assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── auth.js
│       ├── dashboard.js
│       ├── expenses.js
│       ├── income.js
│       ├── accounts.js
│       ├── goals.js
│       ├── scan.js
│       └── profile.js
│
└── templates/                      # HTML templates
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── expenses.html
    ├── income.html
    ├── accounts.html
    ├── goals.html
    ├── scan.html
    └── profile.html
```

## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- MySQL 5.7 or higher
- XAMPP (recommended for local MySQL)

### Installation

1. **Clone the repository**
   ```bash
   cd f:\projects\CN\will of d 1\finance
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   - Start XAMPP and ensure MySQL is running
   - Create the database:
   ```bash
   mysql -u root < schema.sql
   ```

5. **Configure environment variables** (create `.env` file)
   ```
   FLASK_ENV=development
   FLASK_DEBUG=True
   DATABASE_URL=mysql+pymysql://root:password@localhost/finance_db
   JWT_SECRET_KEY=your-secret-key-here
   ```

6. **Run the application**
   ```bash
   python app.py
   ```
   
   The application will be available at `http://localhost:5000`

## 📦 Dependencies

### Core Framework
- Flask 3.0.0 - Web framework
- Flask-SQLAlchemy 3.1.1 - ORM
- Flask-CORS 4.0.0 - CORS support

### Authentication & Security
- Flask-Bcrypt 1.0.1 - Password hashing
- Flask-JWT-Extended 4.6.0 - JWT authentication
- cryptography 42.0.0 - Encryption

### Data Processing & ML
- numpy 1.26.4 - Numerical computing
- pandas 2.2.0 - Data analysis
- scikit-learn 1.4.0 - Machine learning
- pytesseract 0.3.13 - OCR (requires Tesseract)

### Database & Utilities
- PyMySQL 1.1.0 - MySQL connector
- python-dotenv 1.0.0 - Environment variables
- Pillow 12.0.0 - Image processing

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. Register a new account at `/auth/register`
2. Login to get a JWT token at `/auth/login`
3. Include token in Authorization header: `Bearer <token>`

## 🗄️ Database

The application uses MySQL with the following main tables:
- `users` - User accounts and profiles
- `expenses` - Expense records
- `income` - Income records
- `accounts` - Linked bank accounts
- `budgets` - Budget goals
- `transactions` - All financial transactions
- `notifications` - User notifications

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout

### Dashboard
- `GET /api/dashboard` - Get dashboard overview

### Expenses
- `GET /api/expenses` - List expenses
- `POST /api/expenses` - Create expense
- `PUT /api/expenses/<id>` - Update expense
- `DELETE /api/expenses/<id>` - Delete expense

### Income
- `GET /api/income` - List income records
- `POST /api/income` - Create income
- `PUT /api/income/<id>` - Update income
- `DELETE /api/income/<id>` - Delete income

### Insights & Predictions
- `GET /api/insights` - Get financial insights
- `GET /api/prediction` - Get expense predictions

### Reports
- `GET /api/reports` - Generate financial reports
- `POST /api/reports/export` - Export report

### Accounts
- `GET /api/accounts` - List linked accounts
- `POST /api/accounts` - Link new account

## 🤖 Machine Learning Features

### Expense Prediction
Uses scikit-learn Linear Regression to forecast future expenses based on historical data.

### Savings Prediction
Calculates projected savings based on income and expense trends.

### Automatic Categorization
Categorizes transactions using keyword matching and pattern recognition.

## 📱 Frontend

The application includes a web interface with:
- Responsive dashboard
- Expense tracking form
- Income management
- Receipt scanning (OCR)
- Report generation
- Budget tracking
- Profile management

## 🔧 Configuration

Edit `config.py` to customize:
- Database connection settings
- JWT secret key
- Flask environment
- Feature toggles
- API settings

## 🛠️ Development

### Running Tests
```bash
python -m pytest
```

### Database Migrations
```bash
python migrate_db.py
```

### Starting Development Server
```bash
python app.py
# or with debug mode
FLASK_DEBUG=True flask run
```

## 📝 Logging

The application logs to `app.log`. Check this file for debugging information.

## 🐛 Troubleshooting

### MySQL Connection Error
- Ensure XAMPP MySQL is running
- Check database URL in `.env`
- Verify MySQL credentials

### Module Not Found Errors
- Activate virtual environment: `.\.venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### OCR Not Working
- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Update `TESSERACT_PATH` in config if needed

## 📄 License

This project is private and for personal use.

## 👨‍💻 Support

For issues or questions, check the application logs or contact the development team.
