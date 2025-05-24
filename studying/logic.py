import mysql.connector
from datetime import datetime, timedelta, date
from collections import defaultdict
import os
import json
from database.connection import get_connection
from mysql.connector import Error

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKLY_GOAL = 35  # 5 hours per day * 7 days

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
    MIN_HOURS_PER_DAY = 4  # Minimum hours required to count as a good study day
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

    return {
        'current': current_streak,
        'longest': longest_streak,
        'minimumHours': MIN_HOURS_PER_DAY
    }

def get_study_data():
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return {
                'dailyData': [],
                'movingAvgData': [],
                'weeklyComparison': {'current': 0, 'last': 0, 'change': 0},
                'topicBalance': [],
                'hourlyData': [],
                'goalProgress': {
                    'current': 0,
                    'goal': WEEKLY_GOAL,
                    'percentage': 0,
                    'daysElapsed': 0,
                    'daysRemaining': 7,
                    'hoursRemaining': WEEKLY_GOAL,
                    'avgHoursNeeded': WEEKLY_GOAL / 7,
                    'dailyBreakdown': []
                },
                'streaks': {'current': 0, 'longest': 0, 'minimumHours': 4}
            }
        
        # Get current and last week ranges
        current_week_start, current_week_end = get_current_week_range()
        last_week_start, last_week_end = get_last_week_range()
        
        # Daily Data with improved date handling
        c.execute('''
            SELECT DATE(date) as date, 
                   SUM(hours) as total_hours,
                   GROUP_CONCAT(DISTINCT subject SEPARATOR ',') as subjects
            FROM studying_entries
            WHERE user_id = %s
            GROUP BY DATE(date)
            ORDER BY date
        ''', (current_user,))
        
        daily_data = []
        for row in c.fetchall():
            date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
            daily_data.append({
                'date': date_str,
                'hours': float(row['total_hours']) if row['total_hours'] else 0
            })
        
        # Calculate streaks
        streaks = calculate_streaks(daily_data)
        
        # Calculate moving average
        moving_avg_data = calculate_moving_average(daily_data)
        
        # Current Week Total with daily breakdown and improved date handling
        c.execute('''
            SELECT DATE(date) as date, 
                   SUM(hours) as total_hours,
                   GROUP_CONCAT(DISTINCT subject SEPARATOR ',') as subjects
            FROM studying_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
            GROUP BY DATE(date)
            ORDER BY date
        ''', (current_week_start, current_week_end, current_user))
        
        current_week_daily = []
        for row in c.fetchall():
            date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
            current_week_daily.append({
                'date': date_str,
                'hours': float(row['total_hours']) if row['total_hours'] else 0
            })
        
        current_week_hours = sum(day['hours'] for day in current_week_daily)
        
        # Calculate days remaining in the week
        today = datetime.now().date()
        days_elapsed = (today - datetime.strptime(current_week_start, '%Y-%m-%d').date()).days + 1
        days_remaining = 7 - days_elapsed
        
        # Calculate average hours needed per remaining day
        hours_remaining = WEEKLY_GOAL - current_week_hours
        avg_hours_needed = hours_remaining / days_remaining if days_remaining > 0 else 0
        
        # Last Week Total with improved date handling
        c.execute('''
            SELECT SUM(hours) as total_hours
            FROM studying_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
        ''', (last_week_start, last_week_end, current_user))
        last_week_result = c.fetchone()
        last_week_hours = float(last_week_result['total_hours']) if last_week_result['total_hours'] else 0
        
        # Calculate weekly change
        weekly_change = ((current_week_hours - last_week_hours) / last_week_hours * 100) if last_week_hours > 0 else 0
        
        # Topic Balance - Last 30 days with improved date handling
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT subject, 
                   SUM(hours) as total_hours,
                   COUNT(DISTINCT DATE(date)) as days_studied
            FROM studying_entries
            WHERE date >= %s AND user_id = %s
            GROUP BY subject
            ORDER BY total_hours DESC
        ''', (thirty_days_ago, current_user))
        
        topic_data = []
        for row in c.fetchall():
            topic_data.append({
                'topic': row['subject'],
                'hours': float(row['total_hours']) if row['total_hours'] else 0,
                'days_studied': row['days_studied']
            })
        
        # Calculate total hours for percentage
        total_hours = sum(t['hours'] for t in topic_data)
        topic_balance = [{
            'topic': t['topic'],
            'hours': t['hours'],
            'percentage': round((t['hours'] / total_hours * 100), 1) if total_hours else 0,
            'days_studied': t['days_studied']
        } for t in topic_data]
        
        # Most Common Study Hours
        c.execute('''
            SELECT subject, COUNT(*) as count
            FROM studying_entries
            WHERE user_id = %s
            GROUP BY subject
            ORDER BY count DESC
        ''', (current_user,))
        
        hourly_data = [{'hour': i, 'hours': row['count']} for i, row in enumerate(c.fetchall())]
        
        return {
            'dailyData': daily_data,
            'movingAvgData': moving_avg_data,
            'weeklyComparison': {
                'current': round(current_week_hours, 1),
                'last': round(last_week_hours, 1),
                'change': round(weekly_change, 1)
            },
            'topicBalance': topic_balance,
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

def add_study_session(data):
    with get_connection() as conn:
        c = conn.cursor()
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return {'error': 'User not authenticated'}
            
        c.execute('''
            INSERT INTO studying_entries (user_id, date, hours, subject, notes)
            VALUES (%s, %s, %s, %s, %s)
        ''', (current_user, data['date'], data['hours'], data['topic'], data.get('notes', '')))
        conn.commit()
        return {'message': 'Study session added successfully'}

def get_today_sessions():
    today = datetime.now().strftime('%Y-%m-%d')
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        c.execute('SELECT * FROM studying_entries WHERE date = %s', (today,))
        rows = c.fetchall()
        return {
            'today': today,
            'sessions': [{
                'id': row['id'],
                'user_id': row['user_id'],
                'date': row['date'],
                'hours': row['hours'],
                'topic': row['subject'],
                'notes': row['notes']
            } for row in rows]
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
        
        # Updated SQL query with proper date handling and GROUP_CONCAT
        c.execute('''
            SELECT DATE(date) as date, 
                   SUM(hours) as total_hours, 
                   GROUP_CONCAT(DISTINCT subject SEPARATOR ',') as subjects
            FROM studying_entries
            WHERE date BETWEEN %s AND %s AND user_id = %s
            GROUP BY DATE(date)
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), current_user))
        
        # Improved data processing with proper date handling
        daily_data = {}
        for row in c.fetchall():
            date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
            subjects = row['subjects'].split(',') if row['subjects'] else []
            daily_data[date_str] = {
                'hours': float(row['total_hours']) if row['total_hours'] else 0,
                'subjects': subjects
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
            day_data = daily_data.get(date_str, {'hours': 0, 'subjects': []})
            
            if is_future:
                intensity = 0
            else:
                hours = day_data['hours']
                if hours == 0:
                    intensity = 0
                elif hours < 3:
                    intensity = 1
                elif hours < 5:
                    intensity = 2
                elif hours < 7:
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
                'subjects': day_data['subjects'],
                'isToday': current_date == today,
                'isWeekend': current_date.weekday() >= 5,
                'isFuture': is_future
            })
        
        current_date += timedelta(days=1)
    
    return calendar_data

def check_database():
    conn = mysql.connector.connect(user='your_username', password='your_password', host='localhost', database='studying')
    c = conn.cursor()
    
    # Check total records
    total = c.execute('SELECT COUNT(*) FROM study_sessions').fetchone()[0]
    print(f'Total records: {total}')
    
    # Get sample data
    print('\nSample data:')
    sample = c.execute('SELECT * FROM study_sessions LIMIT 5').fetchall()
    for row in sample:
        print(row)
    
    conn.close()

def test_data_retrieval():
    try:
        data = get_study_data()
        print("Data retrieved successfully!")
        print("\nSample of daily data:")
        print(json.dumps(data['dailyData'][:5], indent=2))
        print("\nWeekly comparison:")
        print(json.dumps(data['weeklyComparison'], indent=2))
        print("\nTopic balance:")
        print(json.dumps(data['topicBalance'], indent=2))
    except Exception as e:
        print(f"Error retrieving data: {str(e)}")

def init_db():
    """Initialize the studying_entries table using MySQL syntax."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS studying_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    date DATE,
                    subject VARCHAR(100),
                    hours FLOAT,
                    productivity INT,
                    notes TEXT
                )
            ''')
            conn.commit()
    except Error as e:
        print(f"Error initializing studying_entries table: {e}")

def get_common_topics():
    """Get the 7 most common study topics from the database."""
    with get_connection() as conn:
        c = conn.cursor(dictionary=True)
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            return []
        
        c.execute('''
            SELECT subject, COUNT(*) as count
            FROM studying_entries
            WHERE user_id = %s
            GROUP BY subject
            ORDER BY count DESC
            LIMIT 7
        ''', (current_user,))
        
        topics = [row['subject'] for row in c.fetchall()]
        return topics

if __name__ == '__main__':
    test_data_retrieval() 