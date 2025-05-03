from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
DATABASE = 'studying.db'

# ========== Initialisation de la BDD ==========
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
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
        conn.commit()

# ========== Récupérer les données ==========
def get_study_data():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        today = datetime.now().date()
        start_date = today - timedelta(days=6)
        c.execute('''
            SELECT date, SUM(duree)
            FROM studying
            WHERE date BETWEEN ? AND ?
            GROUP BY date
        ''', (start_date.isoformat(), today.isoformat()))
        rows = c.fetchall()

    daily_hours = defaultdict(float)
    for row in rows:
        daily_hours[row[0]] = row[1]

    data = []
    for i in range(7):
        day = (start_date + timedelta(days=i)).isoformat()
        data.append((day, daily_hours[day]))
    return data

# ========== Statistiques ==========
def get_stats(data):
    durations = [d[1] for d in data]
    total = round(sum(durations), 1)
    avg = round(total / 7, 2)
    max_day = max(data, key=lambda x: x[1])
    min_day = min(data, key=lambda x: x[1])
    streak = 0
    for d in reversed(durations):
        if d > 0:
            streak += 1
        else:
            break
    return {
        'total': total,
        'avg': avg,
        'best_day': max_day[0],
        'worst_day': min_day[0],
        'streak': streak
    }

# ========== Page d’accueil principale ==========
@app.route('/', methods=['GET', 'POST'])
def main():
    today = datetime.now().date().isoformat()
    if request.method == 'POST':
        duree = float(request.form['duree'])
        start = request.form['start']
        subject = request.form['subject']
        lieu = request.form['lieu']
        date = today  # Date actuelle automatique

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO studying (date, start, duree, subject, lieu)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, start, duree, subject, lieu))
            conn.commit()
        return redirect(url_for('main'))

    return render_template('main.html', today=today)

# ========== Page dédiée à l’analyse studying ==========
@app.route('/studying')
def studying():
    study_data = get_study_data()
    stats = get_stats(study_data)
    labels = [datetime.fromisoformat(d[0]).strftime('%a %d/%m') for d in study_data]
    durations = [d[1] for d in study_data]

    return render_template('studying.html',
                           labels=labels,
                           durations=durations,
                           stats=stats)



# ========== Lancement ==========
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
