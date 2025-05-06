from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'budget.db')
WEEKLY_GOAL = 500  # Weekly budget goal in dollars

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
            CREATE TABLE IF NOT EXISTS budget_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                amount REAL,
                category TEXT,
                description TEXT
            )
        ''')
        conn.commit()

def calculate_moving_average(data, window=7):
    """Calculate moving average for a list of (date, value) tuples."""
    if not data:
        return []
    
    # Convert to list of tuples for easier processing
    data_list = [(d['date'], d['amount']) for d in data]
    result = []
    
    for i in range(len(data_list)):
        start_idx = max(0, i - window + 1)
        window_data = data_list[start_idx:i + 1]
        avg = sum(amount for _, amount in window_data) / len(window_data)
        result.append({'date': data_list[i][0], 'amount': round(avg, 2)})
    
    return result

def calculate_streaks(daily_data):
    # Convert to dict with date as key and amount as value
    MAX_AMOUNT_PER_DAY = 100  # Maximum amount to count as a good budget day
    budget_dates = {
        entry['date']: entry['amount'] 
        for entry in daily_data 
        if entry['amount'] <= MAX_AMOUNT_PER_DAY
    }

    today = datetime.today().date()
    current_streak = 0
    longest_streak = 0
    streak = 0

    # Calculate current streak
    day = today
    while True:
        date_str = day.strftime("%Y-%m-%d")
        if date_str in budget_dates:
            streak += 1
            day -= timedelta(days=1)
        else:
            if day == today:
                day -= timedelta(days=1)  # ignore today if not within budget
                continue
            break

    current_streak = streak

    # Calculate longest streak
    streak = 0
    previous_day = None
    for d in sorted(budget_dates.keys()):
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
        'maximumAmount': MAX_AMOUNT_PER_DAY
    }

# ========== API Routes ==========
@app.route('/api/budget-data')
def get_budget_data():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Get today's date and calculate date ranges
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_end - timedelta(days=7)
        
        # Get current week's data
        c.execute('''
            SELECT SUM(amount) as total
            FROM budget_entries
            WHERE date BETWEEN ? AND ?
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        current_week_total = c.fetchone()[0] or 0
        
        # Get last week's data
        c.execute('''
            SELECT SUM(amount) as total
            FROM budget_entries
            WHERE date BETWEEN ? AND ?
        ''', (last_week_start.strftime('%Y-%m-%d'), last_week_end.strftime('%Y-%m-%d')))
        last_week_total = c.fetchone()[0] or 0
        
        # Calculate weekly change
        if last_week_total > 0:
            weekly_change = ((current_week_total - last_week_total) / last_week_total) * 100
        else:
            weekly_change = 0
        
        # Get daily data for the last 30 days
        thirty_days_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT date, SUM(amount) as total_amount
            FROM budget_entries
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
        ''', (thirty_days_ago,))
        daily_data = [{'date': row[0], 'amount': row[1] or 0} for row in c.fetchall()]
        
        # Get category balance
        c.execute('''
            SELECT category, SUM(amount) as total_amount
            FROM budget_entries
            WHERE date >= ?
            GROUP BY category
            ORDER BY total_amount DESC
        ''', (thirty_days_ago,))
        category_data = c.fetchall()
        total_amount = sum(row[1] for row in category_data)
        category_balance = [
            {
                'category': row[0],
                'amount': row[1] or 0,
                'percentage': round((row[1] or 0) / total_amount * 100, 1) if total_amount > 0 else 0
            }
            for row in category_data
        ]
        
        # Calculate current streak
        c.execute('''
            SELECT date, SUM(amount) as total_amount
            FROM budget_entries
            GROUP BY date
            ORDER BY date DESC
        ''')
        entries = c.fetchall()
        
        current_streak = 0
        max_amount = 100  # Maximum amount per day for streak
        
        for date_str, amount in entries:
            if amount and amount <= max_amount:
                current_streak += 1
            else:
                break
        
        # Calculate goal progress
        weekly_goal = 500  # $500 per week
        days_remaining = 7 - today.weekday()
        amount_needed = weekly_goal - current_week_total
        avg_amount_needed = amount_needed / days_remaining if days_remaining > 0 else 0
        
        return jsonify({
            'streaks': {
                'current': current_streak,
                'maximumAmount': max_amount
            },
            'goalProgress': {
                'current': current_week_total,
                'goal': weekly_goal,
                'percentage': min(round(current_week_total / weekly_goal * 100, 1), 100),
                'daysRemaining': days_remaining,
                'amountRemaining': amount_needed,
                'avgAmountNeeded': avg_amount_needed
            },
            'weeklyComparison': {
                'change': weekly_change
            },
            'dailyData': daily_data,
            'categoryBalance': category_balance
        })

@app.route('/api/calendar-data')
def get_calendar_data():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        
        # Calculate proper start date to align with Monday
        first_day_of_year = datetime(2025, 1, 1).date()
        # Go back to the Monday of the week containing Jan 1st
        start_date = first_day_of_year - timedelta(days=first_day_of_year.weekday())
        # Calculate end date to ensure we have complete weeks
        end_date = datetime(2025, 12, 31).date()
        last_weekday = end_date.weekday()
        if last_weekday < 6:  # If not Sunday, extend to end of week
            end_date = end_date + timedelta(days=6-last_weekday)
        
        c.execute('''
            SELECT date, SUM(amount) as total_amount, GROUP_CONCAT(category) as categories
            FROM budget_entries
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        daily_data = {row[0]: {'amount': row[1], 'categories': set(row[2].split(',')) if row[2] else set()} 
                     for row in c.fetchall()}
        
        # Generate calendar data
        calendar_data = []
        today = datetime.now().date()
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
                data = daily_data.get(date_str, {'amount': 0, 'categories': set()})
                
                # Calculate intensity based on amount
                amount = data['amount']
                if amount == 0:
                    intensity = 0
                elif amount <= 25:
                    intensity = 1
                elif amount <= 50:
                    intensity = 2
                elif amount <= 75:
                    intensity = 3
                else:
                    intensity = 4
                
                calendar_data.append({
                    'date': date_str,
                    'amount': amount,
                    'categories': list(data['categories']),
                    'intensity': intensity,
                    'isFuture': is_future,
                    'week': week_number,
                    'weekday': current_date.weekday(),  # 0 = Monday, 6 = Sunday
                    'gridColumn': week_number
                })
            
            current_date += timedelta(days=1)
        
        return jsonify({'calendarData': calendar_data})

@app.route('/api/budget-entries', methods=['POST'])
def add_budget_entry():
    data = request.json
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO budget_entries (date, amount, category, description)
            VALUES (?, ?, ?, ?)
        ''', (data['date'], data['amount'], data['category'], data['description']))
        conn.commit()
    return jsonify({'message': 'Budget entry added successfully'})

@app.route('/api/debug-today')
def debug_today():
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM budget_entries WHERE date = ?', (today,))
        rows = c.fetchall()
        return jsonify({
            'today': today,
            'entries': [{
                'id': row[0],
                'date': row[1],
                'amount': row[2],
                'category': row[3],
                'description': row[4]
            } for row in rows]
        })

# ========== Main Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 
