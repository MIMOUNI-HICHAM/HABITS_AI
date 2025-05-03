import sqlite3
from datetime import datetime, timedelta
import random

DATABASE = 'studying.db'

def seed_data():
    subjects = ['Math', 'Coding', 'Physics', 'Langues']
    lieux = ['Maison', 'Bibliothèque', 'Café']
    today = datetime.now().date()

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()

        # Créer la table si elle n'existe pas
        c.execute('''
            CREATE TABLE IF NOT EXISTS studying (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                start TEXT NOT NULL,
                duree REAL NOT NULL,
                subject TEXT NOT NULL,
                lieu TEXT NOT NULL
            )
        ''')

        for i in range(10):  # 10 jours précédents
            day = today - timedelta(days=i)
            for _ in range(random.randint(0, 2)):  # 0 à 2 sessions par jour
                duree = round(random.uniform(0.5, 3.0), 1)
                start_hour = random.randint(7, 20)
                start = f"{start_hour:02d}:{random.randint(0,59):02d}"
                subject = random.choice(subjects)
                lieu = random.choice(lieux)
                c.execute('''
                    INSERT INTO studying (date, start, duree, subject, lieu)
                    VALUES (?, ?, ?, ?, ?)
                ''', (day.isoformat(), start, duree, subject, lieu))

        conn.commit()
        print("✔ Base de données remplie avec des données fictives.")

if __name__ == "__main__":
    seed_data()
