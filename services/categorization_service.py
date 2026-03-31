"""
Categorization Service
Auto-categorizes expenses based on keywords in merchant name or description.
Uses predefined rules and a lightweight NLP approach.
"""
from models import Expense
import re

# Predefined keyword mappings
CATEGORY_RULES = {
    'Food & Dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonalds', 'uber eats', 'doordash', 'grocery', 'whole foods', 'trader joe', 'pub', 'bar', 'grill', 'pizza', 'diner'],
    'Transportation': ['uber', 'lyft', 'gas', 'shell', 'chevron', 'exxon', 'transit', 'mta', 'subway', 'train', 'parking', 'toll', 'amtrak', 'taxi'],
    'Housing': ['rent', 'mortgage', 'hoa', 'property tax', 'home depot', 'lowes', 'ikea', 'furniture'],
    'Utilities': ['electric', 'water', 'gas utility', 'pg&e', 'coned', 'internet', 'comcast', 'xfinity', 'verizon', 'att', 'mobile', 'cell', 'waste', 'trash'],
    'Healthcare': ['doctor', 'hospital', 'pharmacy', 'cvs', 'walgreens', 'clinic', 'dental', 'vision', 'medical', 'copay', 'therapy'],
    'Entertainment': ['movie', 'theater', 'netflix', 'hulu', 'spotify', 'apple tv', 'disney+', 'concert', 'ticket', 'game', 'playstation', 'xbox', 'steam', 'museum'],
    'Shopping': ['amazon', 'target', 'walmart', 'best buy', 'macys', 'nordstrom', 'clothes', 'shoes', 'apparel', 'electronics'],
    'Education': ['tuition', 'school', 'college', 'university', 'bookstore', 'course', 'udemy', 'coursera', 'textbook'],
    'Insurance': ['geico', 'state farm', 'progressive', 'allstate', 'insurance', 'premium'],
    'Savings & Investments': ['vanguard', 'fidelity', 'robinhood', 'coinbase', 'schwab', 'deposit', 'transfer to savings'],
    'Personal Care': ['salon', 'haircut', 'barber', 'spa', 'massage', 'cosmetics', 'sephora', 'ulta', 'gym', 'planet fitness', 'equinox', 'crossfit'],
    'Travel': ['airline', 'delta', 'united', 'american airlines', 'hotel', 'marriott', 'hilton', 'airbnb', 'expedia', 'flight', 'resort'],
    'Subscriptions': ['netflix', 'spotify', 'hulu', 'gym', 'magazine', 'patreon', 'subscription', 'membership', 'duolingo'],
    'Gifts & Donations': ['charity', 'donation', 'gift', 'gofundme', 'red cross', 'flower', 'wedding'],
}

def auto_categorize(merchant_name, description=''):
    """
    Predicts the best category for a transaction based on text.
    First tries explicit keyword matching, defaults to 'Other'.
    """
    text_to_search = f"{merchant_name} {description}".lower()
    
    # Check against rules
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            # Word boundary matching
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_to_search):
                return category
                
    # Fallback if no rules matched
    return 'Other'

def train_or_update_model(user_id):
    """
    Placeholder for ML-based approach. 
    Would fetch all user Expenses, train a NaiveBayes model, and save it.
    Currently returns True as rule-based doesn't need training.
    """
    return True
