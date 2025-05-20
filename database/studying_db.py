import sqlite3
from datetime import datetime, timedelta
import random
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PROJECT_ROOT, 'studying', 'studying.db')

def init_db():
    """Initialize the studying database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Drop existing table if it exists
        c.execute('DROP TABLE IF EXISTS study_sessions')
        
        # Create new table with user_id
        c.execute('''
            CREATE TABLE study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                time TEXT,
                hours REAL,
                topic TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def generate_sessions(date, is_recent):
    """Generate realistic study sessions for a given date."""
    sessions = []
    topics = ['Math', 'Science', 'History', 'Literature', 'Programming', 'Languages']
    locations = ['Library', 'Home', 'Cafe', 'University', 'Study Room']
    
    # Generate 1-4 sessions per day
    num_sessions = random.randint(1, 4) if is_recent else random.randint(0, 3)
    
    for _ in range(num_sessions):
        topic = random.choice(topics)
        location = random.choice(locations)
        hours = round(random.uniform(0.5, 4.0), 1)
        time = f"{random.randint(8, 22):02d}:{random.randint(0, 59):02d}"
        
        sessions.append((
            'hicham',  # user_id
            date.strftime('%Y-%m-%d'),
            time,
            hours,
            topic,
            location
        ))
    
    return sessions

def seed_data():
    """Seed the studying database with realistic data."""
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM study_sessions WHERE user_id = ?', ('hicham',))

        today = datetime.now()
        # Generate data for the entire year up until today
        start_date = today.replace(month=1, day=1)  # Start from January 1st
        days_diff = (today - start_date).days + 1  # Include today

        for i in range(days_diff):
            date = start_date + timedelta(days=i)
            
            # Simulate missed days (no studying)
            if random.random() < 0.2:
                continue

            # Generate 1-4 sessions per day
            num_sessions = random.randint(1, 4)
            for _ in range(num_sessions):
                topic = random.choice(['Math', 'Science', 'History', 'Literature', 'Programming', 'Languages'])
                location = random.choice(['Library', 'Home', 'Cafe', 'University', 'Study Room'])
                hours = round(random.uniform(0.5, 4.0), 1)
                time = f"{random.randint(8, 22):02d}:{random.randint(0, 59):02d}"
                
                c.execute('''
                    INSERT INTO study_sessions (user_id, date, time, hours, topic, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('hicham', date.strftime('%Y-%m-%d'), time, hours, topic, location))

        conn.commit()
        print("✅ Study data updated for user 'hicham' with full year data.")

if __name__ == '__main__':
    seed_data() 