import mysql.connector
from datetime import datetime, timedelta, date
import os
from database.connection import get_connection
from mysql.connector import Error
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

def calculate_moving_average(data, window=7):
    """Calculate moving average for a list of (date, value) tuples."""
    if not data:
        return []
    
    data_list = [(d['date'], d['amount']) for d in data]
    result = []
    
    for i in range(len(data_list)):
        start_idx = max(0, i - window + 1)
        window_data = data_list[start_idx:i + 1]
        avg = sum(amount for _, amount in window_data) / len(window_data)
        result.append({'date': data_list[i][0], 'amount': round(avg, 2)})
    
    return result

def calculate_streaks(daily_data):
    MAX_AMOUNT_PER_DAY = 100
    budget_dates = {
        entry['date']: entry['amount'] 
        for entry in daily_data 
        if entry['amount'] <= MAX_AMOUNT_PER_DAY
    }

    today = datetime.today().date()
    current_streak = 0
    longest_streak = 0
    streak = 0

    day = today
    while True:
        date_str = day.strftime("%Y-%m-%d")
        if date_str in budget_dates:
            streak += 1
            day -= timedelta(days=1)
        else:
            if day == today:
                day -= timedelta(days=1)
                continue
            break

    current_streak = streak

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

def get_budget_data():
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return {
                'streaks': {'current': 0, 'maximumAmount': 100},
                'goalProgress': {
                    'current': 0,
                    'goal': WEEKLY_GOAL,
                    'percentage': 0,
                    'daysRemaining': 7,
                    'amountRemaining': WEEKLY_GOAL,
                    'avgAmountNeeded': WEEKLY_GOAL / 7
                },
                'weeklyComparison': {'change': 0},
                'dailyData': [],
                'categoryBalance': []
            }
        
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_end - timedelta(days=7)
        
        c.execute('''
            SELECT SUM(amount) as total
            FROM budget_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
        ''', (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'), current_user))
        current_week_total = c.fetchone()['total'] or 0
        
        c.execute('''
            SELECT SUM(amount) as total
            FROM budget_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
        ''', (last_week_start.strftime('%Y-%m-%d'), last_week_end.strftime('%Y-%m-%d'), current_user))
        last_week_total = c.fetchone()['total'] or 0
        
        weekly_change = ((current_week_total - last_week_total) / last_week_total) * 100 if last_week_total > 0 else 0
        
        thirty_days_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT date, SUM(amount) as total_amount
            FROM budget_entries
            WHERE date >= %s AND user_id = %s
            GROUP BY date
            ORDER BY date
        ''', (thirty_days_ago, current_user))
        daily_data = [{'date': row['date'], 'amount': row['total_amount'] or 0} for row in c.fetchall()]
        
        c.execute('''
            SELECT category, SUM(amount) as total_amount
            FROM budget_entries
            WHERE date >= %s AND user_id = %s
            GROUP BY category
            ORDER BY total_amount DESC
        ''', (thirty_days_ago, current_user))
        category_data = c.fetchall()
        total_amount = sum(row['total_amount'] for row in category_data)
        category_balance = [
            {
                'category': row['category'],
                'amount': row['total_amount'] or 0,
                'percentage': round((row['total_amount'] or 0) / total_amount * 100, 1) if total_amount > 0 else 0
            }
            for row in category_data
        ]
        
        c.execute('''
            SELECT date, SUM(amount) as total_amount
            FROM budget_entries
            WHERE user_id = %s
            GROUP BY date
            ORDER BY date DESC
        ''', (current_user,))
        entries = c.fetchall()
        
        current_streak = 0
        max_amount = 100
        
        for row in entries:
            if row['total_amount'] and row['total_amount'] <= max_amount:
                current_streak += 1
            else:
                break
        
        days_remaining = 7 - today.weekday()
        amount_needed = WEEKLY_GOAL - current_week_total
        avg_amount_needed = amount_needed / days_remaining if days_remaining > 0 else 0
        
        return {
            'streaks': {
                'current': current_streak,
                'maximumAmount': max_amount
            },
            'goalProgress': {
                'current': current_week_total,
                'goal': WEEKLY_GOAL,
                'percentage': min(round(current_week_total / WEEKLY_GOAL * 100, 1), 100),
                'daysRemaining': days_remaining,
                'amountRemaining': amount_needed,
                'avgAmountNeeded': avg_amount_needed
            },
            'weeklyComparison': {
                'change': weekly_change
            },
            'dailyData': daily_data,
            'categoryBalance': category_balance
        }

def get_calendar_data():
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return []
        
        first_day_of_year = datetime(2025, 1, 1).date()
        start_date = first_day_of_year - timedelta(days=first_day_of_year.weekday())
        end_date = datetime(2025, 12, 31).date()
        last_weekday = end_date.weekday()
        if last_weekday < 6:
            end_date = end_date + timedelta(days=6-last_weekday)
        
        c.execute('''
            SELECT DATE(date) as date, 
                   SUM(amount) as total_amount, 
                   GROUP_CONCAT(DISTINCT category SEPARATOR ',') as categories
            FROM budget_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
            GROUP BY DATE(date)
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), current_user))
        
        daily_data = {}
        for row in c.fetchall():
            date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
            categories = row['categories'].split(',') if row['categories'] else []
            daily_data[date_str] = {
                'amount': float(row['total_amount']) if row['total_amount'] else 0,
                'categories': categories
            }
    
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
            day_data = daily_data.get(date_str, {'amount': 0, 'categories': []})
            
            if is_future:
                intensity = 0
            else:
                amount = day_data['amount']
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
                'day': current_date.day,
                'month': current_date.month,
                'year': current_date.year,
                'weekday': current_date.weekday(),  # 0 = Monday, 6 = Sunday
                'week': week_number,
                'gridColumn': week_number,
                'amount': day_data['amount'],
                'intensity': intensity,
                'categories': day_data['categories'],
                'isToday': current_date == today,
                'isWeekend': current_date.weekday() >= 5,
                'isFuture': is_future
            })
        
        current_date += timedelta(days=1)
    
    return calendar_data

def add_budget_entry(data):
    with get_connection() as conn:
        c = conn.cursor()
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return {'error': 'User not authenticated'}
            
        c.execute('''
            INSERT INTO budget_entries (user_id, date, amount, category, description)
            VALUES (%s, %s, %s, %s, %s)
        ''', (current_user, data['date'], data['amount'], data['category'], data['description']))
        conn.commit()
    return {'message': 'Budget entry added successfully'}

def get_today_entries():
    today = datetime.now().strftime('%Y-%m-%d')
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        c.execute('SELECT * FROM budget_entries WHERE date = %s', (today,))
        rows = c.fetchall()
        return {
            'today': today,
            'entries': [{
                'id': row['id'],
                'date': row['date'],
                'amount': row['amount'],
                'category': row['category'],
                'description': row['description']
            } for row in rows]
        }

def init_db():
    """Initialize the budget_entries table using MySQL syntax."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS budget_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    date DATE,
                    amount FLOAT,
                    category VARCHAR(100),
                    description TEXT
                )
            ''')
            conn.commit()
    except Error as e:
        print(f"Error initializing budget_entries table: {e}") 