import sqlite3
import random
from datetime import datetime, timedelta
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'sports.db')

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sports_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                duration REAL,
                activity TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def pick_activity():
    activities = [
        'Running', 'Swimming', 'Cycling', 'Gym Workout', 
        'Basketball', 'Tennis', 'Yoga', 'HIIT'
    ]
    return random.choice(activities)

def pick_location():
    locations = [
        'Local Gym', 'Park', 'Swimming Pool', 'Home',
        'Sports Center', 'Tennis Court', 'Fitness Studio'
    ]
    return random.choice(locations)

def generate_sessions(start_date, end_date):
    sessions = []
    current_date = start_date
    
    while current_date <= end_date:
        # Skip some days randomly (25% chance after first month)
        if random.random() < 0.25 and (current_date - start_date).days > 30:
            current_date += timedelta(days=1)
            continue
            
        # Generate 1-2 sessions per day
        num_sessions = random.randint(1, 2)
        for _ in range(num_sessions):
            # Random time between 6 AM and 9 PM
            hour = random.randint(6, 21)
            minute = random.choice([0, 15, 30, 45])
            time = f"{hour:02d}:{minute:02d}"
            
            # Duration between 30 minutes and 2 hours
            duration = round(random.uniform(0.5, 2.0), 1)
            
            # Simulate holiday breaks in July and August with reduced activity
            if current_date.month in [7, 8]:
                if random.random() < 0.5:  # 50% chance to skip during holidays
                    continue
                duration *= 0.7  # Shorter sessions during holidays
            
            sessions.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'time': time,
                'duration': duration,
                'activity': pick_activity(),
                'location': pick_location()
            })
        
        current_date += timedelta(days=1)
    
    return sessions

def seed_data():
    init_db()
    
    # Generate data for the year 2025
    start_date = datetime(2025, 1, 1).date()
    end_date = datetime(2025, 12, 31).date()
    
    sessions = generate_sessions(start_date, end_date)
    
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.executemany('''
            INSERT INTO sports_sessions (date, time, duration, activity, location)
            VALUES (:date, :time, :duration, :activity, :location)
        ''', sessions)
        conn.commit()
    
    print("Year of realistic sports activity data inserted.")

if __name__ == '__main__':
    seed_data() 