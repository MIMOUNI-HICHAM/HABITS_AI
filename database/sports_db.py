import sqlite3
import random
from datetime import datetime, timedelta
import os

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PROJECT_ROOT, 'sports', 'sports.db')

def init_db():
    """Initialize the sports database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Drop existing table if it exists
        c.execute('DROP TABLE IF EXISTS sports_sessions')
        
        # Create new table with user_id
        c.execute('''
            CREATE TABLE sports_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                date TEXT,
                time TEXT,
                duration REAL,
                activity TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def generate_sessions(start_date, end_date):
    """Generate realistic sports sessions between two dates."""
    sessions = []
    activities = ['Running', 'Cycling', 'Swimming', 'Gym', 'Yoga', 'Basketball']
    locations = ['Park', 'Gym', 'Pool', 'Home', 'Sports Center']
    
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends occasionally
        if current_date.weekday() >= 5 and random.random() < 0.3:
            current_date += timedelta(days=1)
            continue
            
        # Generate 0-2 sessions per day
        num_sessions = random.randint(0, 2)
        
        for _ in range(num_sessions):
            activity = random.choice(activities)
            location = random.choice(locations)
            duration = round(random.uniform(0.5, 3.0), 1)
            time = f"{random.randint(6, 20):02d}:{random.randint(0, 59):02d}"
            
            sessions.append({
                'user_id': 'hicham',
                'date': current_date.strftime('%Y-%m-%d'),
                'time': time,
                'duration': duration,
                'activity': activity,
                'location': location
            })
        
        current_date += timedelta(days=1)
    
    return sessions

def seed_data():
    """Seed the sports database with realistic data."""
    init_db()
    
    # Generate data for the entire year up until today
    today = datetime.now()
    start_date = today.replace(month=1, day=1)  # Start from January 1st
    end_date = today
    
    sessions = []
    activities = ['Running', 'Cycling', 'Swimming', 'Gym', 'Yoga', 'Basketball']
    locations = ['Park', 'Gym', 'Pool', 'Home', 'Sports Center']
    
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends occasionally
        if current_date.weekday() >= 5 and random.random() < 0.3:
            current_date += timedelta(days=1)
            continue
            
        # Generate 0-2 sessions per day
        num_sessions = random.randint(0, 2)
        
        for _ in range(num_sessions):
            activity = random.choice(activities)
            location = random.choice(locations)
            duration = round(random.uniform(0.5, 3.0), 1)
            time = f"{random.randint(6, 20):02d}:{random.randint(0, 59):02d}"
            
            sessions.append({
                'user_id': 'hicham',
                'date': current_date.strftime('%Y-%m-%d'),
                'time': time,
                'duration': duration,
                'activity': activity,
                'location': location
            })
        
        current_date += timedelta(days=1)
    
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Delete existing data for user 'hicham'
        c.execute('DELETE FROM sports_sessions WHERE user_id = ?', ('hicham',))
        
        c.executemany('''
            INSERT INTO sports_sessions (user_id, date, time, duration, activity, location)
            VALUES (:user_id, :date, :time, :duration, :activity, :location)
        ''', sessions)
        conn.commit()
    
    print("✅ Sports activity data updated for user 'hicham' with full year data.")

if __name__ == '__main__':
    seed_data() 