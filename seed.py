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

# Location preference rules
def pick_location(hour):
    if hour < 18:
        return random.choices(['coffee', 'library'], weights=[0.7, 0.3])[0]
    elif hour < 22:
        return random.choices(['coffee', 'library', 'house'], weights=[0.4, 0.4, 0.2])[0]
    else:
        return 'house'

def random_study_session(date):
    hour = random.choices(range(17, 24), weights=[5, 10, 20, 25, 20, 10, 10])[0]
    minute = random.choice([0, 15, 30, 45])
    time = f"{hour:02}:{minute:02}"
    topic = random.choices(['coding', 'math', 'coding', 'math', 'coding', 'other'], weights=[3, 3, 3, 3, 3, 1])[0]
    hours = round(random.uniform(0.5, 3), 1)
    location = pick_location(hour)
    return (date.strftime('%Y-%m-%d'), time, hours, topic, location)

def seed_data():
    init_db()  # Make sure the table exists
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM study_sessions')

        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            if random.random() < 0.25:
                continue
            for _ in range(random.choice([1, 1, 2])):
                session = random_study_session(date)
                c.execute('''
                    INSERT INTO study_sessions (date, time, hours, topic, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', session)

        conn.commit()
        print("✅ Seed data inserted.")

if __name__ == '__main__':
    seed_data()
