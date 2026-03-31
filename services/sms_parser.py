"""
SMS Parsing Service
Extracts transaction details (amount, type, merchant) from bank SMS text.
"""
import re

def parse_bank_sms(text: str) -> dict:
    """
    Parses a typical bank/credit card SMS to extract transaction data.
    e.g., "Rs. 500.00 spent on your HDFC Card ending 1234 at Starbucks."
    e.g., "Your a/c no. XXXX is credited with INR 10,000 on 12-Oct by Salary."
    """
    text = text.replace('\n', ' ').strip()
    
    # 1. Extract Amount (look for currencies or generic decimals)
    # Patterns: Rs. 500.00, INR 500, $500, 500 USD, 500.00
    amount = 0.0
    amount_matches = re.findall(r'(?:Rs\.?|INR|\$|£|€)?\s*(\d+(?:[.,]\d{1,2})?)', text, re.IGNORECASE)
    
    if amount_matches:
        try:
            # Clean up comma separators in numbers before float cast
            raw_val = amount_matches[0].replace(',', '')
            amount = float(raw_val)
        except ValueError:
            amount = 0.0
            
    # 2. Determine Transaction Type (Income vs Expense)
    t_type = 'expense'
    lower_text = text.lower()
    
    income_keywords = ['credited', 'received', 'deposited', 'salary', 'refund', 'added']
    expense_keywords = ['debited', 'spent', 'withdrawn', 'paid', 'purchased', 'sent', 'deducted']
    
    # Simple check for keywords
    if any(keyword in lower_text for keyword in income_keywords):
        t_type = 'income'
    elif any(keyword in lower_text for keyword in expense_keywords):
        t_type = 'expense'
        
    # 3. Extract Merchant / Source
    # Usually after words like "at", "to", "info:", "from" (for income)
    merchant = 'Unknown Merchant/Source'
    
    if t_type == 'expense' and (' at ' in lower_text or ' to ' in lower_text):
        # Look for "at [Merchant]" or "to [Merchant]"
        match = re.search(r'(?:at|to)\s+([A-Za-z0-9 ]+?)(?:\.|\s+on|\s+using|a/c)', text, re.IGNORECASE)
        if match:
            merchant = match.group(1).strip()
    elif t_type == 'income' and 'from' in lower_text:
        match = re.search(r'from\s+([A-Za-z0-9 ]+?)(?:\.|\s+on|\s+to)', text, re.IGNORECASE)
        if match:
            merchant = match.group(1).strip()
            
    # Fallback if regex missed it, just use the first 50 chars of the SMS
    if merchant == 'Unknown Merchant/Source':
        merchant = text[:50] + '...'
        
    return {
        'amount': amount,
        'type': t_type,
        'merchant': merchant,
        'raw_text': text
    }
