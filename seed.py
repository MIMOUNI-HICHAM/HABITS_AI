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

def pick_location(hour):
    if hour < 18:
        return random.choices(['library', 'coffee'], weights=[0.6, 0.4])[0]
    elif hour < 22:
        return random.choices(['house', 'library', 'coffee'], weights=[0.4, 0.3, 0.3])[0]
    return 'house'

def pick_topic(day_index):
    # Simulate focus rotation during the week
    topics = ['coding', 'math', 'ai', 'ml', 'stats', 'other']
    weights = [5, 4, 3, 2, 2, 1] if day_index % 7 < 5 else [3, 3, 3, 2, 2, 3]
    return random.choices(topics, weights=weights)[0]

def random_time():
    hour = random.choices(range(8, 24), weights=[2]*4 + [4]*6 + [3]*6)[0]
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02}:{minute:02}", hour

def generate_sessions(date, is_recent=False):
    sessions = []
    day_index = date.weekday()
    sessions_count = random.choices([1, 2, 3], weights=[6, 3, 1])[0]

    if is_recent:
        sessions_count = random.choices([1, 2, 3], weights=[2, 4, 4])[0]

    for _ in range(sessions_count):
        time_str, hour = random_time()
        topic = pick_topic(day_index)
        location = pick_location(hour)
        hours = round(random.uniform(1, 3.5), 1)
        sessions.append((date.strftime('%Y-%m-%d'), time_str, hours, topic, location))
    return sessions

def seed_data():
    init_db()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM study_sessions')

        today = datetime.now()
        for i in range(365):
            date = today - timedelta(days=i)

            # Simulate holiday breaks
            if date.month in [7, 8] and random.random() < 0.6:
                continue  # summer break

            # Simulate missed days (burnout, weekend)
            if random.random() < 0.25 and i > 30:
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
