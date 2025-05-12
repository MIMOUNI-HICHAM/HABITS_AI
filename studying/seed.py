import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'studying.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                hours REAL,
                topic TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def generate_sessions(date, is_recent=False):
    sessions = []
    topics = ['Mathematics', 'Physics', 'Computer Science', 'Literature', 'History']
    locations = ['Library', 'Home', 'Cafe', 'University', 'Study Room']
    
    # Generate 1-3 sessions per day
    num_sessions = random.randint(1, 3) if is_recent else random.randint(0, 2)
    
    for _ in range(num_sessions):
        # Generate time between 8 AM and 10 PM
        hour = random.randint(8, 22)
        minute = random.choice(['00', '15', '30', '45'])
        time = f"{hour:02d}:{minute}"
        
        # Generate duration between 1 and 4 hours
        hours = round(random.uniform(1.0, 4.0), 1)
        
        session = (
            date.strftime('%Y-%m-%d'),
            time,
            hours,
            random.choice(topics),
            random.choice(locations)
        )
        sessions.append(session)
    
    return sessions

def seed_data():
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM study_sessions')

        today = datetime.now()
        for i in range(365):  # Generate a year of data
            date = today - timedelta(days=i)

            # Simulate holiday breaks (less studying during holidays)
            if date.month in [7, 8] and random.random() < 0.6:
                continue  # summer break

            # Simulate missed days (no studying)
            if random.random() < 0.2 and i > 30:
                continue

            is_recent = i < 30  # last 30 days should have full data
            for session in generate_sessions(date, is_recent):
                c.execute('''
                    INSERT INTO study_sessions (date, time, hours, topic, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', session)

        conn.commit()
        print("✅ Year of realistic study data inserted.")

if __name__ == '__main__':
    seed_data() 