from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
DATABASE = 'studying.db'

# ========== Database Initialization ==========
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

# ========== Get Study Data ==========
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

# ========== Statistics ==========
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

# ========== Main Page ==========
@app.route('/', methods=['GET', 'POST'])
def main():
    today = datetime.now().date().isoformat()
    if request.method == 'POST':
        duree = float(request.form['duree'])
        start = request.form['start']
        subject = request.form['subject']
        lieu = request.form['lieu']
        date = today

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO studying (date, start, duree, subject, lieu)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, start, duree, subject, lieu))
            conn.commit()
        return redirect(url_for('main'))

    return render_template('main.html', today=today)

# ========== Studying Analytics Page ==========
@app.route('/studying')
def studying():
    # Get study data
    study_data = get_study_data()
    
    # Prepare chart data
    labels = [datetime.fromisoformat(d[0]).strftime('%d-%b') for d in study_data]
    durations = [d[1] for d in study_data]
    
    # Calculate percentages
    GOAL_PER_DAY = 1.0
    chart_data = [min(int(h/GOAL_PER_DAY*100), 100) for h in durations]
    
    # Performance metrics
    last_week_percent = int(sum(chart_data) / len(chart_data))
    this_week_percent = last_week_percent
    today_percent = chart_data[-1]
    
    # All-time average
    with sqlite3.connect(DATABASE) as conn:
        all_rows = conn.execute('SELECT date, SUM(duree) FROM studying GROUP BY date').fetchall()
    days = [r[1] for r in all_rows]
    studied_days = sum(1 for h in days if h > 0)
    all_time_average = int(studied_days / len(days) * 100) if days else 0
    
    # Calendar data
    today = datetime.now().date()
    first_of_mo = today.replace(day=1)
    _, days_in_month = divmod((first_of_mo.replace(month=first_of_mo.month%12+1, day=1) - first_of_mo).days, 1)
    studied_set = {row[0] for row in all_rows if row[1] > 0}
    
    calendar_days = []
    for day in range(1, days_in_month+1):
        date_str = first_of_mo.replace(day=day).isoformat()
        calendar_days.append({
            'day': day,
            'studied': date_str in studied_set
        })
    
    # History data with formatted dates
    history = []
    for d in study_data:
        date_obj = datetime.fromisoformat(d[0])
        history.append({
            'date': date_obj.strftime('%Y-%m-%d'),
            'day_name': date_obj.strftime('%A'),
            'completed': (d[1] > 0)
        })
    
    return render_template('studying.html',
        chart_labels=labels,
        chart_data=chart_data,
        last_week_percent=last_week_percent,
        this_week_percent=this_week_percent,
        today_percent=today_percent,
        all_time_average=all_time_average,
        calendar_days=calendar_days,
        history=history,
        current_date=datetime.now().strftime('%B %d, %Y')
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)