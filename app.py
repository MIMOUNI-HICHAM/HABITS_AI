from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict
import os

app = Flask(__name__)
DATABASE = 'studying.db'
WEEKLY_GOAL = 28  # Updated to 28 hours per week

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

def calculate_streaks(daily_data):
    # Convert to dict with date as key and hours as value
    MIN_HOURS_PER_DAY = 4  # Minimum hours required to count as a study day
    studied_dates = {
        entry['date']: entry['hours'] 
        for entry in daily_data 
        if entry['hours'] >= MIN_HOURS_PER_DAY
    }

    today = datetime.today().date()
    current_streak = 0
    longest_streak = 0
    streak = 0

    # Calculate current streak
    day = today
    while True:
        date_str = day.strftime("%Y-%m-%d")
        if date_str in studied_dates:
            streak += 1
            day -= timedelta(days=1)
        else:
            if day == today:
                day -= timedelta(days=1)  # ignore today if not studied
                continue
            break

    current_streak = streak

    # Calculate longest streak
    streak = 0
    previous_day = None
    for d in sorted(studied_dates.keys()):
        current_day = datetime.strptime(d, "%Y-%m-%d").date()
        if previous_day is None or current_day == previous_day + timedelta(days=1):
            streak += 1
        else:
            longest_streak = max(longest_streak, streak)
            streak = 1
        previous_day = current_day
    longest_streak = max(longest_streak, streak)

    # Add debug information
    print(f"Debug - Streak calculation:")
    print(f"Minimum hours required: {MIN_HOURS_PER_DAY}")
    print(f"Days meeting minimum: {len(studied_dates)}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")

    return {
        'current': current_streak,
        'longest': longest_streak,
        'minimumHours': MIN_HOURS_PER_DAY  # Include this in response for frontend display
    }

def get_calendar_data(daily_data):
    """Generate calendar data for the heatmap visualization."""
    # Initialize calendar data structure
    calendar_data = []
    today = datetime.now().date()
    
    # Get the start of the current year
    start_date = datetime(today.year, 1, 1).date()
    # Get the end of the current year
    end_date = datetime(today.year, 12, 31).date()
    
    # Create a dictionary of study data for quick lookup
    study_data = {
        entry['date']: {
            'hours': entry['hours'],
            'topics': [],  # Will be populated from topic data
            'sessions': []  # Will be populated from session data
        }
        for entry in daily_data
    }
    
    # Get detailed session data for each day
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        for date_str in study_data.keys():
            c.execute('''
                SELECT time, hours, topic, location
                FROM study_sessions
                WHERE date = ?
                ORDER BY time
            ''', (date_str,))
            sessions = c.fetchall()
            study_data[date_str]['sessions'] = [
                {
                    'time': session[0],
                    'hours': session[1],
                    'topic': session[2],
                    'location': session[3]
                }
                for session in sessions
            ]
            # Get unique topics for the day
            study_data[date_str]['topics'] = list(set(session[2] for session in sessions))
    
    # Generate calendar data
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        day_data = study_data.get(date_str, {'hours': 0, 'topics': [], 'sessions': []})
        
        # Calculate color intensity (0-4)
        hours = day_data['hours']
        if hours == 0:
            intensity = 0
        elif hours < 2:
            intensity = 1
        elif hours < 4:
            intensity = 2
        elif hours < 6:
            intensity = 3
        else:
            intensity = 4
        
        calendar_data.append({
            'date': date_str,
            'day': current_date.day,
            'month': current_date.month,
            'year': current_date.year,
            'weekday': current_date.weekday(),  # 0 = Monday, 6 = Sunday
            'week': current_date.isocalendar()[1],  # ISO week number
            'hours': hours,
            'intensity': intensity,
            'topics': day_data['topics'],
            'sessions': day_data['sessions'],
            'isToday': current_date == today,
            'isWeekend': current_date.weekday() >= 5
        })
        
        current_date += timedelta(days=1)
    
    return calendar_data

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
        
        # Calculate streaks
        streaks = calculate_streaks(daily_data)
        print(f"Debug - Streaks: {streaks}")
        
        # Calculate moving average
        moving_avg_data = calculate_moving_average(daily_data)
        print(f"Debug - Moving average data count: {len(moving_avg_data)}")
        
        # Current Week Total with daily breakdown
        c.execute('''
            SELECT date, SUM(hours) as total_hours
            FROM study_sessions
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (current_week_start, current_week_end))
        current_week_daily = [{'date': row[0], 'hours': row[1]} for row in c.fetchall()]
        current_week_hours = sum(day['hours'] for day in current_week_daily)
        print(f"Debug - Current week hours: {current_week_hours}")
        
        # Calculate days remaining in the week
        today = datetime.now().date()
        days_elapsed = (today - datetime.strptime(current_week_start, '%Y-%m-%d').date()).days + 1
        days_remaining = 7 - days_elapsed
        
        # Calculate average hours needed per remaining day
        hours_remaining = WEEKLY_GOAL - current_week_hours
        avg_hours_needed = hours_remaining / days_remaining if days_remaining > 0 else 0
        
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
        
        # Calendar Heatmap Data - Full Year
        calendar_data = get_calendar_data(daily_data)
        print(f"Debug - Calendar data count: {len(calendar_data)}")
        
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
            'calendarData': calendar_data,  # Updated calendar data
            'goalProgress': {
                'current': round(current_week_hours, 1),
                'goal': WEEKLY_GOAL,
                'percentage': min(round((current_week_hours / WEEKLY_GOAL * 100), 1), 100),
                'daysElapsed': days_elapsed,
                'daysRemaining': days_remaining,
                'hoursRemaining': round(hours_remaining, 1),
                'avgHoursNeeded': round(avg_hours_needed, 1),
                'dailyBreakdown': current_week_daily
            },
            'streaks': streaks
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