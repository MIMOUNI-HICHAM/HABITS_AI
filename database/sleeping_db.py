import sqlite3
from datetime import datetime, timedelta
import random
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PROJECT_ROOT, 'sleeping', 'sleeping.db')

def init_db():
    """Initialize the sleeping database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Drop existing table if it exists
        c.execute('DROP TABLE IF EXISTS sleep_sessions')
        
        # Create new table with user_id
        c.execute('''
            CREATE TABLE sleep_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                time TEXT,
                hours REAL,
                quality TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def generate_sessions(date, is_recent):
    """Generate realistic sleep sessions for a given date."""
    sessions = []
    qualities = ['Good', 'Fair', 'Poor']
    locations = ['Home', 'Hotel', 'Friend\'s']
    
    # Generate 1-2 sessions per day
    num_sessions = random.randint(1, 2) if is_recent else random.randint(0, 1)
    
    for _ in range(num_sessions):
        hours = round(random.uniform(4, 10), 1)
        quality = random.choice(qualities)
        location = random.choice(locations)
        time = f"{random.randint(20, 23):02d}:{random.randint(0, 59):02d}"
        
        sessions.append((
            'hicham',  # user_id
            date.strftime('%Y-%m-%d'),
            time,
            hours,
            quality,
            location
        ))
    
    return sessions

def seed_data():
    """Seed the sleeping database with realistic data."""
    print(f"Creating database at: {DATABASE}")
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM sleep_sessions WHERE user_id = ?', ('hicham',))

        today = datetime.now()
        # Generate data for the entire year up until today
        start_date = today.replace(month=1, day=1)  # Start from January 1st
        days_diff = (today - start_date).days + 1  # Include today

        for i in range(days_diff):
            date = start_date + timedelta(days=i)

            # Simulate missed days (travel, insomnia)
            if random.random() < 0.1:
                continue

            # Generate 1-2 sessions per day
            num_sessions = random.randint(1, 2)
            for _ in range(num_sessions):
                hours = round(random.uniform(4, 10), 1)
                quality = random.choice(['Good', 'Fair', 'Poor'])
                location = random.choice(['Home', 'Hotel', 'Friend\'s'])
                time = f"{random.randint(20, 23):02d}:{random.randint(0, 59):02d}"
                
                c.execute('''
                    INSERT INTO sleep_sessions (user_id, date, time, hours, quality, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('hicham', date.strftime('%Y-%m-%d'), time, hours, quality, location))

        conn.commit()
        print("✅ Sleep data updated for user 'hicham' with full year data.")

if __name__ == '__main__':
    seed_data() 