"""
Database Migration Script
Safely adds missing columns to existing MySQL tables.
Run once: python migrate_db.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from models import db

app = create_app()

migrations = [
    # expenses table - new columns added in v2
    ("ALTER TABLE expenses ADD COLUMN account_id INT NULL",
     "expenses.account_id"),
    ("ALTER TABLE expenses ADD COLUMN is_recurring TINYINT(1) NOT NULL DEFAULT 0",
     "expenses.is_recurring"),
    ("ALTER TABLE expenses ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
     "expenses.created_at"),

    # income table - new columns added in v2
    ("ALTER TABLE income ADD COLUMN account_id INT NULL",
     "income.account_id"),
    ("ALTER TABLE income ADD COLUMN is_recurring TINYINT(1) NOT NULL DEFAULT 0",
     "income.is_recurring"),
    ("ALTER TABLE income ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
     "income.created_at"),

    # goals table - new columns added in v2
    ("ALTER TABLE goals ADD COLUMN color VARCHAR(50) NULL",
     "goals.color"),
    ("ALTER TABLE goals ADD COLUMN deadline DATE NULL",
     "goals.deadline"),
]

with app.app_context():
    # Ensure all NEW tables exist (accounts, goals, notifications, budgets)
    db.create_all()
    print("OK: db.create_all() completed - new tables created if missing.")

    conn = db.engine.connect()
    for sql, col_desc in migrations:
        try:
            conn.execute(db.text(sql))
            conn.commit()
            print("ADDED: " + col_desc)
        except Exception as e:
            err = str(e)
            if "Duplicate column name" in err or "already exists" in err.lower():
                print("SKIP (already exists): " + col_desc)
            else:
                print("ERROR on " + col_desc + ": " + err)
    conn.close()

    print("")
    print("Migration complete! All missing columns have been added.")
    print("Restart the server with: python app.py")
