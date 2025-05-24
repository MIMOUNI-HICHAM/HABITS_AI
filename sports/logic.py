import mysql.connector
from datetime import datetime, timedelta, date
from collections import defaultdict
import os
import logging
from .utils import get_current_week_range, get_last_week_range, calculate_moving_average
from database.connection import get_connection
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKLY_GOAL = 10  # Weekly goal in hours

# Minimum duration for streak calculation
MIN_DURATION_PER_DAY = 0.5  # Minimum duration (30 minutes) required to count as an active day

def init_db():
    """Initialize the database with required tables if they don't exist."""
    try:
        logger.info("Initializing sports database...")
        with get_connection() as conn:
            c = conn.cursor()
            # Create table if it doesn't exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS sports_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    duration FLOAT NOT NULL,
                    activity VARCHAR(100) NOT NULL,
                    intensity VARCHAR(50),
                    notes TEXT,
                    INDEX idx_user_date (user_id, date)
                )
            ''')
            conn.commit()
            logger.info("Sports database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise Exception(f"Failed to initialize database: {str(e)}")

def execute_query(query, params=()):
    """Execute a database query and return results."""
    try:
        logger.debug(f"Executing query: {query} with params: {params}")
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute(query, params)
            results = c.fetchall()
            logger.debug(f"Query returned {len(results)} results")
            return results
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise

def execute_update(query, params=()):
    """Execute a database update and commit changes."""
    try:
        logger.debug(f"Executing update: {query} with params: {params}")
        with get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            logger.debug("Update executed successfully")
    except Exception as e:
        logger.error(f"Error executing update: {str(e)}")
        raise

def calculate_streaks(daily_data):
    """Calculate current and longest streaks from daily data."""
    active_dates = {
        entry['date']: entry['hours'] 
        for entry in daily_data 
        if entry['hours'] >= MIN_DURATION_PER_DAY
    }

    today = datetime.today().date()
    current_streak = 0
    longest_streak = 0
    streak = 0

    # Calculate current streak
    day = today
    while True:
        date_str = day.strftime("%Y-%m-%d")
        if date_str in active_dates:
            streak += 1
            day -= timedelta(days=1)
        else:
            if day == today:
                day -= timedelta(days=1)  # ignore today if not active
                continue
            break

    current_streak = streak

    # Calculate longest streak
    streak = 0
    previous_day = None
    for d in sorted(active_dates.keys()):
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
        'minimumHours': MIN_DURATION_PER_DAY
    }

def get_sports_data():
    """Get all sports data for the dashboard."""
    try:
        logger.info("Fetching sports data...")
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            
            # Get current user from session
            from flask import session
            current_user = session.get('user_id')
            if not current_user:
                logger.warning("No user found in session")
                raise Exception("User not authenticated")
            
            logger.info(f"Fetching data for user {current_user}")
            
            # Get current and last week ranges
            current_week_start, current_week_end = get_current_week_range()
            last_week_start, last_week_end = get_last_week_range()
            logger.debug(f"Week ranges - Current: {current_week_start} to {current_week_end}, Last: {last_week_start} to {last_week_end}")
            
            # Daily Data with proper date formatting
            logger.debug("Fetching daily data...")
            c.execute('''
                SELECT DATE(date) as date, 
                       ROUND(SUM(duration), 1) as total_hours,
                       GROUP_CONCAT(DISTINCT activity SEPARATOR ',') as activities
                FROM sports_sessions
                WHERE user_id = %s
                GROUP BY DATE(date)
                ORDER BY date
            ''', (current_user,))
            
            # Convert rows to dictionary with date as key
            daily_data = {}
            rows = c.fetchall()
            logger.debug(f"Found {len(rows)} daily entries")
            
            for row in rows:
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
                activities = row['activities'].split(',') if row['activities'] else []
                daily_data[date_str] = {
                    'hours': float(row['total_hours']) if row['total_hours'] else 0,
                    'activities': activities
                }
            
            # Convert to list format for compatibility
            daily_data_list = [{'date': date, 'hours': data['hours']} for date, data in daily_data.items()]
            logger.debug(f"Processed {len(daily_data_list)} daily entries")
            
            # Calculate streaks
            logger.debug("Calculating streaks...")
            streaks = calculate_streaks(daily_data_list)
            logger.debug(f"Streaks calculated: {streaks}")
            
            # Calculate moving average
            logger.debug("Calculating moving average...")
            moving_avg_data = calculate_moving_average(daily_data_list)
            logger.debug(f"Moving average calculated for {len(moving_avg_data)} days")
            
            # Current Week Total with daily breakdown
            logger.debug("Fetching current week data...")
            c.execute('''
                SELECT DATE(date) as date, 
                       ROUND(SUM(duration), 1) as total_hours,
                       GROUP_CONCAT(DISTINCT activity SEPARATOR ',') as activities
                FROM sports_sessions
                WHERE date BETWEEN %s AND %s AND user_id = %s
                GROUP BY DATE(date)
                ORDER BY date
            ''', (current_week_start, current_week_end, current_user))
            
            current_week_daily = []
            current_week_hours = 0
            current_week_rows = c.fetchall()
            logger.debug(f"Found {len(current_week_rows)} entries for current week")
            
            for row in current_week_rows:
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
                hours = float(row['total_hours']) if row['total_hours'] else 0
                current_week_daily.append({'date': date_str, 'hours': hours})
                current_week_hours += hours
            
            logger.debug(f"Current week total hours: {current_week_hours}")
            
            # Calculate days remaining in the week
            today = datetime.now().date()
            days_elapsed = (today - datetime.strptime(current_week_start, '%Y-%m-%d').date()).days + 1
            days_remaining = max(0, 7 - days_elapsed)
            logger.debug(f"Days elapsed: {days_elapsed}, Days remaining: {days_remaining}")
            
            # Calculate average hours needed per remaining day
            hours_remaining = max(0, WEEKLY_GOAL - current_week_hours)
            avg_hours_needed = hours_remaining / days_remaining if days_remaining > 0 else 0
            logger.debug(f"Hours remaining: {hours_remaining}, Average needed: {avg_hours_needed}")
            
            # Last Week Total
            logger.debug("Fetching last week data...")
            c.execute('''
                SELECT ROUND(SUM(duration), 1) as total_hours
                FROM sports_sessions
                WHERE date BETWEEN %s AND %s AND user_id = %s
            ''', (last_week_start, last_week_end, current_user))
            last_week_hours = float(c.fetchone()['total_hours'] or 0)
            logger.debug(f"Last week total hours: {last_week_hours}")
            
            # Calculate weekly change
            weekly_change = ((current_week_hours - last_week_hours) / last_week_hours * 100) if last_week_hours > 0 else 0
            logger.debug(f"Weekly change: {weekly_change}%")
            
            # Activity Balance - Last 30 days
            logger.debug("Fetching activity balance...")
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            c.execute('''
                SELECT activity, ROUND(SUM(duration), 1) as total_hours
                FROM sports_sessions
                WHERE date >= %s AND user_id = %s
                GROUP BY activity
                ORDER BY total_hours DESC
            ''', (thirty_days_ago, current_user))
            activity_data = [{'activity': row['activity'], 'hours': float(row['total_hours'] or 0)} for row in c.fetchall()]
            logger.debug(f"Found {len(activity_data)} activities in last 30 days")
            
            # Calculate total hours for percentage
            total_hours = sum(t['hours'] for t in activity_data)
            activity_balance = [{
                'activity': t['activity'],
                'hours': t['hours'],
                'percentage': round((t['hours'] / total_hours * 100), 1) if total_hours > 0 else 0
            } for t in activity_data]
            
            # Most Active Hours - Using actual time
            logger.debug("Fetching hourly data...")
            c.execute('''
                SELECT 
                    HOUR(time) as hour,
                    ROUND(SUM(duration), 1) as total_hours
                FROM sports_sessions
                WHERE user_id = %s
                GROUP BY HOUR(time)
                ORDER BY hour
            ''', (current_user,))
            hourly_data = [{'hour': row['hour'], 'hours': float(row['total_hours'] or 0)} for row in c.fetchall()]
            logger.debug(f"Found activity in {len(hourly_data)} different hours")
            
            logger.info("Successfully fetched all sports data")
            return {
                'dailyData': daily_data_list,
                'movingAvgData': moving_avg_data,
                'weeklyComparison': {
                    'current': round(current_week_hours, 1),
                    'last': round(last_week_hours, 1),
                    'change': round(weekly_change, 1)
                },
                'activityBalance': activity_balance,
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
    except Exception as e:
        logger.error(f"Error in get_sports_data: {str(e)}", exc_info=True)
        raise Exception(f"Error in get_sports_data: {str(e)}")

def get_calendar_data():
    """Generate calendar data for the heatmap visualization."""
    try:
        logger.info("Generating calendar data...")
        calendar_data = []
        today = datetime.now().date()
        
        # Get current user from session
        from flask import session
        current_user = session.get('user_id')
        if not current_user:
            logger.warning("No user found in session")
            raise Exception("User not authenticated")
        
        logger.info(f"Generating calendar for user {current_user}")
        
        # Get the current year
        current_year = datetime.now().year
        logger.debug(f"Using year: {current_year}")
        
        # Calculate proper start date to align with Monday
        first_day_of_year = datetime(current_year, 1, 1).date()
        # Go back to the Monday of the week containing Jan 1st
        start_date = first_day_of_year - timedelta(days=first_day_of_year.weekday())
        # Calculate end date to ensure we have complete weeks
        end_date = datetime(current_year, 12, 31).date()
        last_weekday = end_date.weekday()
        if last_weekday < 6:  # If not Sunday, extend to end of week
            end_date = end_date + timedelta(days=6-last_weekday)
        
        logger.debug(f"Calendar range: {start_date} to {end_date}")
        
        # Fetch all sports data for the year
        logger.debug("Fetching sports data for calendar...")
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute('''
                SELECT DATE(date) as date,
                       ROUND(SUM(duration), 1) as total_hours,
                       GROUP_CONCAT(DISTINCT activity SEPARATOR ',') as activities
                FROM sports_sessions
                WHERE user_id = %s AND YEAR(date) = %s
                GROUP BY DATE(date)
            ''', (current_user, current_year))
            
            # Convert rows to dictionary with date as key
            sports_data = {}
            rows = c.fetchall()
            logger.debug(f"Found {len(rows)} entries for calendar")
            
            for row in rows:
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], (datetime, date)) else row['date']
                sports_data[date_str] = {
                    'hours': float(row['total_hours']) if row['total_hours'] else 0,
                    'activities': row['activities'].split(',') if row['activities'] else []
                }
        
        # Generate calendar data
        logger.debug("Generating calendar grid...")
        current_date = start_date
        week = 0
        while current_date <= end_date:
            if current_date.weekday() == 0:  # Monday
                week += 1
            
            date_str = current_date.strftime('%Y-%m-%d')
            is_future = current_date > today
            
            # Get data for this date
            day_data = sports_data.get(date_str, {'hours': 0, 'activities': []})
            
            # Calculate intensity based on duration and activity type
            hours = day_data['hours']
            if hours == 0:
                intensity = 0
            elif hours < 0.5:  # Less than 30 minutes
                intensity = 1  # Light activity
            elif hours < 1:    # Less than 1 hour
                intensity = 2  # Moderate activity
            elif hours < 1.5:  # Less than 1.5 hours
                intensity = 3  # Intense activity
            else:
                intensity = 4  # Very intense activity
            
            calendar_data.append({
                'date': date_str,
                'week': week,
                'weekday': current_date.weekday(),
                'gridColumn': week,
                'hours': hours,
                'intensity': intensity,
                'isFuture': is_future,
                'activities': day_data['activities']
            })
            
            current_date += timedelta(days=1)
        
        logger.info(f"Generated calendar data with {len(calendar_data)} entries")
        return calendar_data
    except Exception as e:
        logger.error(f"Error in get_calendar_data: {str(e)}", exc_info=True)
        raise Exception(f"Error in get_calendar_data: {str(e)}") 