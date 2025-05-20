import sqlite3
from datetime import datetime, timedelta
import random
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PROJECT_ROOT, 'budget', 'budget.db')

def init_db():
    """Initialize the budget database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Drop existing table if it exists
        c.execute('DROP TABLE IF EXISTS budget_entries')
        
        # Create new table with user_id
        c.execute('''
            CREATE TABLE budget_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                amount REAL,
                category TEXT,
                description TEXT
            )
        ''')
        conn.commit()

def generate_entries(date, is_recent):
    """Generate realistic budget entries for a given date."""
    entries = []
    categories = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Bills']
    
    # Generate 1-3 entries per day
    num_entries = random.randint(1, 3) if is_recent else random.randint(0, 2)
    
    for _ in range(num_entries):
        category = random.choice(categories)
        amount = round(random.uniform(5, 100), 2)
        description = f"{category} expense"
        
        entries.append((
            'hicham',  # user_id
            date.strftime('%Y-%m-%d'),
            amount,
            category,
            description
        ))
    
    return entries

def seed_data():
    """Seed the budget database with realistic data."""
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM budget_entries WHERE user_id = ?', ('hicham',))

        today = datetime.now()
        # Generate data for the entire year up until today
        start_date = today.replace(month=1, day=1)  # Start from January 1st
        days_diff = (today - start_date).days + 1  # Include today

        for i in range(days_diff):
            date = start_date + timedelta(days=i)

            # Simulate missed days (no spending)
            if random.random() < 0.25:
                continue

            # Generate 1-3 entries per day
            num_entries = random.randint(1, 3)
            for _ in range(num_entries):
                category = random.choice(['Food', 'Transport', 'Entertainment', 'Shopping', 'Bills'])
                amount = round(random.uniform(5, 100), 2)
                description = f"{category} expense"
                
                c.execute('''
                    INSERT INTO budget_entries (user_id, date, amount, category, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('hicham', date.strftime('%Y-%m-%d'), amount, category, description))

        conn.commit()
        print("✅ Budget data updated for user 'hicham' with full year data.")

if __name__ == '__main__':
    seed_data() 