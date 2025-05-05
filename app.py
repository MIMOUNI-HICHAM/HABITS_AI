from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict
import os

app = Flask(__name__)
DATABASE = 'studying.db'
WEEKLY_GOAL = 10  # hours per week

def get_current_week_range():
    today = datetime.combine(date.today(), datetime.min.time())
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')

def get_last_week_range():
    today = datetime.combine(date.today(), datetime.min.time())
    start_of_week = today - timedelta(days=today.weekday())
    last_week_start = start_of_week - timedelta(days=7)
    last_week_end = start_of_week - timedelta(days=1)
    return last_week_start.strftime('%Y-%m-%d'), last_week_end.strftime('%Y-%m-%d')

# ========== Database Initialization ==========
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

def calculate_moving_average(data, window=7):
    """Calculate moving average for a list of (date, value) tuples."""
    if not data:
        return []
    
    # Convert to list of tuples for easier processing
    data_list = [(d['date'], d['hours']) for d in data]
    result = []
    
    for i in range(len(data_list)):
        start_idx = max(0, i - window + 1)
        window_data = data_list[start_idx:i + 1]
        avg = sum(hours for _, hours in window_data) / len(window_data)
        result.append({'date': data_list[i][0], 'hours': round(avg, 2)})
    
    return result

def calculate_streaks(dates_with_hours):
    """Calculate current and longest streaks."""
    if not dates_with_hours:
        return {'current': 0, 'longest': 0}
    
    # Convert dates to datetime objects and sort
    dates = sorted([datetime.strptime(d['date'], '%Y-%m-%d') for d in dates_with_hours])
    today = datetime.today().date()
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    for i in range(len(dates)):
        if i == 0:
            temp_streak = 1
        else:
            diff = (dates[i] - dates[i-1]).days
            if diff == 1:
                temp_streak += 1
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        # Check if this is part of current streak
        if dates[i].date() == today:
            current_streak = temp_streak
        elif dates[i].date() == today - timedelta(days=1):
            current_streak = temp_streak
    
    return {
        'current': current_streak,
        'longest': longest_streak
    }

# ========== API Routes ==========
@app.route('/api/study-data')
def get_study_data():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Get current and last week ranges
        current_week_start, current_week_end = get_current_week_range()
        last_week_start, last_week_end = get_last_week_range()
        
        print(f"Debug - Week ranges:")
        print(f"Current week: {current_week_start} to {current_week_end}")
        print(f"Last week: {last_week_start} to {last_week_end}")
        
        # Daily Data
        c.execute('''
            SELECT date, SUM(hours) as total_hours
            FROM study_sessions
            GROUP BY date
            ORDER BY date
        ''')
        daily_data = [{'date': row[0], 'hours': row[1]} for row in c.fetchall()]
        print(f"Debug - Daily data count: {len(daily_data)}")
        
        # Calculate moving average
        moving_avg_data = calculate_moving_average(daily_data)
        print(f"Debug - Moving average data count: {len(moving_avg_data)}")
        
        # Current Week Total
        c.execute('''
            SELECT SUM(hours) as total_hours
            FROM study_sessions
            WHERE date BETWEEN ? AND ?
        ''', (current_week_start, current_week_end))
        current_week_hours = c.fetchone()[0] or 0
        print(f"Debug - Current week hours: {current_week_hours}")
        
        # Last Week Total
        c.execute('''
            SELECT SUM(hours) as total_hours
            FROM study_sessions
            WHERE date BETWEEN ? AND ?
        ''', (last_week_start, last_week_end))
        last_week_hours = c.fetchone()[0] or 0
        print(f"Debug - Last week hours: {last_week_hours}")
        
        # Calculate weekly change
        weekly_change = ((current_week_hours - last_week_hours) / last_week_hours * 100) if last_week_hours > 0 else 0
        
        # Topic Balance - Last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT topic, SUM(hours) as total_hours
            FROM study_sessions
            WHERE date >= ?
            GROUP BY topic
            ORDER BY total_hours DESC
        ''', (thirty_days_ago,))
        topic_data = [{'topic': row[0], 'hours': row[1]} for row in c.fetchall()]
        print(f"Debug - Topic data count: {len(topic_data)}")
        
        # Calculate total hours for percentage
        total_hours = sum(t['hours'] for t in topic_data)
        topic_balance = [{
            'topic': t['topic'],
            'hours': t['hours'],
            'percentage': round((t['hours'] / total_hours * 100), 1) if total_hours else 0
        } for t in topic_data]
        
        # Most Productive Hours
        c.execute('''
            SELECT substr(time, 1, 2) as hour,
                   SUM(hours) as total_hours
            FROM study_sessions
            GROUP BY hour
            ORDER BY hour
        ''')
        hourly_data = [{'hour': int(row[0]), 'hours': row[1]} for row in c.fetchall()]
        print(f"Debug - Hourly data count: {len(hourly_data)}")
        
        # Calendar Heatmap Data - Last 90 days
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT date, SUM(hours) as total_hours
            FROM study_sessions
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
        ''', (ninety_days_ago,))
        heatmap_data = [{'date': row[0], 'hours': row[1]} for row in c.fetchall()]
        print(f"Debug - Heatmap data count: {len(heatmap_data)}")
        
        response_data = {
            'dailyData': daily_data,
            'movingAvgData': moving_avg_data,
            'weeklyComparison': {
                'current': round(current_week_hours, 1),
                'last': round(last_week_hours, 1),
                'change': round(weekly_change, 1)
            },
            'topicBalance': topic_balance,
            'hourlyData': hourly_data,
            'heatmapData': heatmap_data,
            'goalProgress': {
                'current': round(current_week_hours, 1),
                'goal': WEEKLY_GOAL,
                'percentage': min(round((current_week_hours / WEEKLY_GOAL * 100), 1), 100)
            }
        }
        
        print("Debug - Response data structure:", list(response_data.keys()))
        return jsonify(response_data)

@app.route('/api/study-sessions', methods=['POST'])
def add_study_session():
    data = request.json
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO study_sessions (date, time, hours, topic, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['date'], data['time'], data['hours'], data['topic'], data['location']))
        conn.commit()
    return jsonify({'message': 'Study session added successfully'})

@app.route('/api/debug-today')
def debug_today():
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM study_sessions WHERE date = ?', (today,))
        rows = c.fetchall()
        return jsonify({
            'today': today,
            'sessions': [{
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'hours': row[3],
                'topic': row[4],
                'location': row[5]
            } for row in rows]
        })

# ========== Main Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)