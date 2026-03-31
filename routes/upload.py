"""
Upload & Parse Routes
Handles OCR receipt scanning and CSV data import parsing.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import pandas as pd
import io

from models import db, Expense, Income, Account
from utils.helpers import success_response, error_response
from services.ocr_service import extract_receipt_data
from services.categorization_service import auto_categorize
from services.notification_service import on_expense_added
from services.sms_parser import parse_bank_sms
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/api/upload/receipt', methods=['POST'])
@jwt_required()
def scan_receipt():
    """Receive an image, run OCR, auto-categorize, and return form data."""
    if 'file' not in request.files:
        return error_response('No file part')
        
    file = request.files['file']
    if file.filename == '':
        return error_response('No selected file')
        
    if file and allowed_file(file.filename):
        # Read byte stream into memory
        file_bytes = file.read()
        
        # Call OCR service
        extracted_data = extract_receipt_data(file_bytes)
        
        if 'error' in extracted_data and 'Tesseract' in extracted_data['error']:
            return error_response(extracted_data['error'], 500)
            
        merchant = extracted_data.get('merchant', 'Unknown Merchant')
        amount = extracted_data.get('amount', 0.0)
        date = extracted_data.get('date', '')
        
        # Auto-categorize based on Merchant name
        category = auto_categorize(merchant, "OCR Scanner")
        
        return success_response({
            'amount': amount,
            'merchant': merchant,
            'date': date,
            'suggested_category': category
        }, 'Receipt successfully scanned')
        
    return error_response('Invalid file type')


@upload_bp.route('/api/upload/csv', methods=['POST'])
@jwt_required()
def import_csv():
    """Receive a CSV, parse with pandas, auto-categorize, and bulk insert."""
    user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return error_response('No file uploaded')
        
    file = request.files['file']
    account_id = request.form.get('account_id')
    
    if not file.filename.endswith('.csv'):
         return error_response('File must be a CSV')
         
    try:
        # Require account_id to assign these imported rows to a specific bank/wallet
        if account_id:
            acc = Account.query.filter_by(id=account_id, user_id=user_id).first()
            if not acc:
                return error_response("Invalid account selected")
            account_id = acc.id
        else:
            return error_response("Must provide an account_id to import into.")
            
        # Parse CSV into Pandas DataFrame
        df = pd.read_csv(io.StringIO(file.stream.read().decode("UTF8")), header=0)
        
        # Expected columns: Date, Description, Amount, Type (Income/Expense)
        required_cols = {'date', 'description', 'amount', 'type'}
        df.columns = [c.lower().strip() for c in df.columns]
        
        if not required_cols.issubset(set(df.columns)):
            return error_response(f"CSV missing mandatory columns: {required_cols}")
            
        imported_count = 0
        new_expenses = []
        
        for index, row in df.iterrows():
            amt = abs(float(row['amount']))
            date_val = pd.to_datetime(row['date']).date()
            desc = str(row['description'])
            t_type = str(row['type']).lower()
            
            if 'income' in t_type or 'credit' in t_type:
                new_inc = Income(
                    user_id=user_id,
                    account_id=account_id,
                    amount=amt,
                    source=desc[:100],  # use description as source
                    description=desc,
                    date=date_val
                )
                db.session.add(new_inc)
            else:
                # Auto categorize expense
                category = auto_categorize(merchant_name="", description=desc)
                new_exp = Expense(
                    user_id=user_id,
                    account_id=account_id,
                    amount=amt,
                    category=category,
                    description=desc,
                    date=date_val
                )
                db.session.add(new_exp)
                new_expenses.append(new_exp)
                
            imported_count += 1
            
        db.session.commit()
        
        # Trigger notification hooks AFTER commit (so IDs are available)
        for exp in new_expenses:
            try:
                on_expense_added(exp)
            except Exception:
                pass  # Non-critical — notifications should not break imports
        
        return success_response(f"Successfully imported {imported_count} transactions.")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"CSV Parsing Error: {str(e)}")


@upload_bp.route('/api/upload/sms', methods=['POST'])
@jwt_required()
def import_sms():
    """Receive SMS text, parse it using regex, auto-categorize, and return extracted data or save."""
    data = request.get_json()
    
    if not data or 'sms_text' not in data:
        return error_response('No sms_text provided')
        
    sms_text = data['sms_text']
    parsed = parse_bank_sms(sms_text)
    
    if parsed['amount'] <= 0:
        return error_response('Failed to detect a valid amount from the SMS.')
        
    # Auto-categorize
    if parsed['type'] == 'expense':
        parsed['suggested_category'] = auto_categorize(parsed['merchant'], parsed['raw_text'])
    else:
        parsed['suggested_category'] = 'Income'
        
    return success_response(parsed, 'SMS successfully parsed')
