from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict
import os

app = Flask(__name__)
DATABASE = 'sleeping.db'
WEEKLY_GOAL = 49  # 7 hours per day * 7 days

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
    MIN_HOURS_PER_DAY = 6  # Minimum hours required to count as a good sleep day
    slept_dates = {
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
        if date_str in slept_dates:
            streak += 1
            day -= timedelta(days=1)
        else:
            if day == today:
                day -= timedelta(days=1)  # ignore today if not slept
                continue
            break

    current_streak = streak

    # Calculate longest streak
    streak = 0
    previous_day = None
    for d in sorted(slept_dates.keys()):
        current_day = datetime.strptime(d, "%Y-%m-%d").date()
        if previous_day is None or current_day == previous_day + timedelta(days=1):
            streak += 1
        else:
            longest_streak = max(longest_streak, streak)
            streak = 1
        previous_day = current_day
    longest_streak = max(longest_streak, streak)

    return {
        'current': current_streak,
        'longest': longest_streak,
        'minimumHours': MIN_HOURS_PER_DAY
    }

# ========== API Routes ==========
@app.route('/api/sleep-data')
def get_sleep_data():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Get current and last week ranges
        current_week_start, current_week_end = get_current_week_range()
        last_week_start, last_week_end = get_last_week_range()
        
        # Daily Data
        c.execute('''
            SELECT date, SUM(hours) as total_hours
            FROM sleep_sessions
            GROUP BY date
            ORDER BY date
        ''')
        daily_data = [{'date': row[0], 'hours': row[1]} for row in c.fetchall()]
        
        # Calculate streaks
        streaks = calculate_streaks(daily_data)
        
        # Calculate moving average
        moving_avg_data = calculate_moving_average(daily_data)
        
        # Current Week Total with daily breakdown
        c.execute('''
            SELECT date, SUM(hours) as total_hours
            FROM sleep_sessions
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (current_week_start, current_week_end))
        current_week_daily = [{'date': row[0], 'hours': row[1]} for row in c.fetchall()]
        current_week_hours = sum(day['hours'] for day in current_week_daily)
        
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
            FROM sleep_sessions
            WHERE date BETWEEN ? AND ?
        ''', (last_week_start, last_week_end))
        last_week_hours = c.fetchone()[0] or 0
        
        # Calculate weekly change
        weekly_change = ((current_week_hours - last_week_hours) / last_week_hours * 100) if last_week_hours > 0 else 0
        
        # Sleep Quality Balance - Last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT quality, SUM(hours) as total_hours
            FROM sleep_sessions
            WHERE date >= ?
            GROUP BY quality
            ORDER BY total_hours DESC
        ''', (thirty_days_ago,))
        quality_data = [{'quality': row[0], 'hours': row[1]} for row in c.fetchall()]
        
        # Calculate total hours for percentage
        total_hours = sum(t['hours'] for t in quality_data)
        quality_balance = [{
            'quality': t['quality'],
            'hours': t['hours'],
            'percentage': round((t['hours'] / total_hours * 100), 1) if total_hours else 0
        } for t in quality_data]
        
        # Most Common Sleep Hours
        c.execute('''
            SELECT substr(time, 1, 2) as hour,
                   SUM(hours) as total_hours
            FROM sleep_sessions
            GROUP BY hour
            ORDER BY hour
        ''')
        hourly_data = [{'hour': int(row[0]), 'hours': row[1]} for row in c.fetchall()]
        
        response_data = {
            'dailyData': daily_data,
            'movingAvgData': moving_avg_data,
            'weeklyComparison': {
                'current': round(current_week_hours, 1),
                'last': round(last_week_hours, 1),
                'change': round(weekly_change, 1)
            },
            'qualityBalance': quality_balance,
            'hourlyData': hourly_data,
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
        
        return jsonify(response_data)

@app.route('/api/sleep-sessions', methods=['POST'])
def add_sleep_session():
    data = request.json
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO sleep_sessions (date, time, hours, quality, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['date'], data['time'], data['hours'], data['quality'], data['location']))
        conn.commit()
    return jsonify({'message': 'Sleep session added successfully'})

@app.route('/api/debug-today')
def debug_today():
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM sleep_sessions WHERE date = ?', (today,))
        rows = c.fetchall()
        return jsonify({
            'today': today,
            'sessions': [{
                'id': row[0],
                'date': row[1],
                'time': row[2],
                'hours': row[3],
                'quality': row[4],
                'location': row[5]
            } for row in rows]
        })

@app.route('/api/calendar-data')
def api_calendar_data():
    return jsonify(get_calendar_data())

# ========== Main Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sleeping')
def sleeping():
    return render_template('sleeping.html')

def get_calendar_data():
    """Generate calendar data for the heatmap visualization for the year 2025 only."""
    calendar_data = []
    today = datetime.now().date()
    
    # Calculate proper start date to align with Monday
    first_day_of_year = datetime(2025, 1, 1).date()
    # Go back to the Monday of the week containing Jan 1st
    start_date = first_day_of_year - timedelta(days=first_day_of_year.weekday())
    # Calculate end date to ensure we have complete weeks
    end_date = datetime(2025, 12, 31).date()
    last_weekday = end_date.weekday()
    if last_weekday < 6:  # If not Sunday, extend to end of week
        end_date = end_date + timedelta(days=6-last_weekday)
    
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT date, SUM(hours) as total_hours,
                   GROUP_CONCAT(DISTINCT quality) as qualities
            FROM sleep_sessions
            WHERE date BETWEEN ? AND ?
            GROUP BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        sleep_data = {}
        for row in c.fetchall():
            date_str = row[0]
            sleep_data[date_str] = {
                'hours': row[1],
                'qualities': row[2].split(',') if row[2] else []
            }
    
    # Generate calendar data
    current_date = start_date
    week_number = 1
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        is_future = current_date > today
        
        # Calculate grid position
        if current_date.weekday() == 0:  # If it's Monday
            week_number += 1
        
        # Only include days from 2025 in the calendar data
        if current_date.year == 2025:
            day_data = sleep_data.get(date_str, {'hours': 0, 'qualities': []})
            
            if is_future:
                intensity = 0
            else:
                hours = day_data['hours']
                if hours == 0:
                    intensity = 0
                elif hours < 6:
                    intensity = 1
                elif hours < 7:
                    intensity = 2
                elif hours < 8:
                    intensity = 3
                else:
                    intensity = 4
            
            calendar_data.append({
                'date': date_str,
                'day': current_date.day,
                'month': current_date.month,
                'year': current_date.year,
                'weekday': current_date.weekday(),  # 0 = Monday, 6 = Sunday
                'week': week_number,
                'gridColumn': week_number,
                'hours': day_data['hours'],
                'intensity': intensity,
                'qualities': day_data['qualities'],
                'isToday': current_date == today,
                'isWeekend': current_date.weekday() >= 5,
                'isFuture': is_future
            })
        
        current_date += timedelta(days=1)
    
    return calendar_data

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 