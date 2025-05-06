import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'budget.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS budget_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                amount REAL,
                category TEXT,
                description TEXT
            )
        ''')
        conn.commit()

def pick_category():
    categories = ['groceries', 'dining', 'transport', 'entertainment', 'utilities', 'shopping']
    weights = [3, 2, 2, 1, 2, 2]
    return random.choices(categories, weights=weights)[0]

def generate_description(category):
    descriptions = {
        'groceries': ['Weekly groceries', 'Food shopping', 'Supermarket run'],
        'dining': ['Restaurant dinner', 'Coffee shop', 'Takeout'],
        'transport': ['Bus fare', 'Train ticket', 'Taxi ride'],
        'entertainment': ['Movie tickets', 'Concert', 'Museum visit'],
        'utilities': ['Electricity bill', 'Water bill', 'Internet bill'],
        'shopping': ['Clothing', 'Electronics', 'Home goods']
    }
    return random.choice(descriptions[category])

def generate_entries(date, is_recent=False):
    entries = []
    entries_count = random.choices([1, 2, 3], weights=[4, 4, 2])[0]

    if is_recent:
        entries_count = random.choices([1, 2, 3], weights=[2, 4, 4])[0]

    for _ in range(entries_count):
        category = pick_category()
        description = generate_description(category)
        amount = round(random.uniform(5, 100), 2)
        entries.append((date.strftime('%Y-%m-%d'), amount, category, description))
    return entries

def seed_data():
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM budget_entries')

        today = datetime.now()
        for i in range(365):  # Generate a year of data
            date = today - timedelta(days=i)

            # Simulate holiday breaks (less spending during holidays)
            if date.month in [7, 8] and random.random() < 0.6:
                continue  # summer break

            # Simulate missed days (no spending)
            if random.random() < 0.25 and i > 30:
                continue

            is_recent = i < 30  # last 30 days should have full data
            for entry in generate_entries(date, is_recent):
                c.execute('''
                    INSERT INTO budget_entries (date, amount, category, description)
                    VALUES (?, ?, ?, ?)
                ''', entry)

        conn.commit()
        print("✅ Year of realistic budget data inserted.")

if __name__ == '__main__':
    seed_data()
