import sqlite3
from datetime import datetime, timedelta
import random
import os

# Get the directory where seed.py is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(CURRENT_DIR, 'sleeping.db')

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sleep_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                hours REAL,
                quality TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def pick_location(hour):
    if hour < 22:
        return random.choices(['bedroom', 'living_room'], weights=[0.8, 0.2])[0]
    return 'bedroom'

def pick_quality(day_index):
    # Simulate sleep quality variation during the week
    qualities = ['deep', 'light', 'restless', 'interrupted', 'refreshing']
    weights = [3, 2, 2, 1, 4] if day_index % 7 < 5 else [4, 2, 1, 1, 3]
    return random.choices(qualities, weights=weights)[0]

def random_time():
    # Combine hours from 21-23 and 0-5
    hours = list(range(21, 24)) + list(range(0, 6))
    hour = random.choices(hours, weights=[2]*3 + [4]*6)[0]
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02}:{minute:02}", hour

def generate_sessions(date, is_recent=False):
    sessions = []
    day_index = date.weekday()
    sessions_count = 1  # One sleep session per day

    time_str, hour = random_time()
    quality = pick_quality(day_index)
    location = pick_location(hour)
    hours = round(random.uniform(5, 9), 1)  # 5-9 hours of sleep
    sessions.append((date.strftime('%Y-%m-%d'), time_str, hours, quality, location))
    return sessions

def seed_data():
    print(f"Creating database at: {DATABASE}")
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM sleep_sessions')

        today = datetime.now()
        for i in range(365):
            date = today - timedelta(days=i)

            # Simulate missed days (travel, insomnia)
            if random.random() < 0.1 and i > 30:
                continue

            is_recent = i < 30  # last 30 days should have full data
            for session in generate_sessions(date, is_recent):
                c.execute('''
                    INSERT INTO sleep_sessions (date, time, hours, quality, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', session)

        conn.commit()
        print("✅ Year of realistic sleep data inserted.")

if __name__ == '__main__':
    seed_data() 