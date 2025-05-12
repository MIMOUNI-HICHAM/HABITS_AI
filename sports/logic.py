from datetime import datetime, timedelta, date
from .config import MIN_DURATION_PER_DAY, WEEKLY_GOAL
from .database import execute_query
from .utils import get_current_week_range, get_last_week_range, calculate_moving_average

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
        # Get current and last week ranges
        current_week_start, current_week_end = get_current_week_range()
        last_week_start, last_week_end = get_last_week_range()
        
        # Daily Data
        daily_data = [
            {'date': row[0], 'hours': row[1] or 0} 
            for row in execute_query('''
                SELECT date, SUM(duration) as total_hours
                FROM sports_sessions
                GROUP BY date
                ORDER BY date
            ''')
        ]
        
        # Calculate streaks
        streaks = calculate_streaks(daily_data)
        
        # Calculate moving average
        moving_avg_data = calculate_moving_average(daily_data)
        
        # Current Week Total with daily breakdown
        current_week_daily = [
            {'date': row[0], 'hours': row[1] or 0} 
            for row in execute_query('''
                SELECT date, SUM(duration) as total_hours
                FROM sports_sessions
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
            ''', (current_week_start, current_week_end))
        ]
        current_week_hours = sum(day['hours'] for day in current_week_daily)
        
        # Calculate days remaining in the week
        today = datetime.now().date()
        days_elapsed = (today - datetime.strptime(current_week_start, '%Y-%m-%d').date()).days + 1
        days_remaining = max(0, 7 - days_elapsed)
        
        # Calculate average hours needed per remaining day
        hours_remaining = max(0, WEEKLY_GOAL - current_week_hours)
        avg_hours_needed = hours_remaining / days_remaining if days_remaining > 0 else 0
        
        # Last Week Total
        last_week_hours = execute_query('''
            SELECT SUM(duration) as total_hours
            FROM sports_sessions
            WHERE date BETWEEN ? AND ?
        ''', (last_week_start, last_week_end))[0][0] or 0
        
        # Calculate weekly change
        weekly_change = ((current_week_hours - last_week_hours) / last_week_hours * 100) if last_week_hours > 0 else 0
        
        # Activity Balance - Last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        activity_data = [
            {'activity': row[0], 'hours': row[1] or 0} 
            for row in execute_query('''
                SELECT activity, SUM(duration) as total_hours
                FROM sports_sessions
                WHERE date >= ?
                GROUP BY activity
                ORDER BY total_hours DESC
            ''', (thirty_days_ago,))
        ]
        
        # Calculate total hours for percentage
        total_hours = sum(t['hours'] for t in activity_data)
        activity_balance = [{
            'activity': t['activity'],
            'hours': t['hours'],
            'percentage': round((t['hours'] / total_hours * 100), 1) if total_hours > 0 else 0
        } for t in activity_data]
        
        # Most Active Hours
        hourly_data = [
            {'hour': int(row[0]), 'hours': row[1] or 0} 
            for row in execute_query('''
                SELECT substr(time, 1, 2) as hour,
                       SUM(duration) as total_hours
                FROM sports_sessions
                GROUP BY hour
                ORDER BY hour
            ''')
        ]
        
        return {
            'dailyData': daily_data,
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
        raise Exception(f"Error in get_sports_data: {str(e)}")

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
    
    sports_data = {}
    for row in execute_query('''
        SELECT date, SUM(duration) as total_hours,
               GROUP_CONCAT(DISTINCT activity) as activities
        FROM sports_sessions
        WHERE date BETWEEN ? AND ?
        GROUP BY date
    ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))):
        date_str = row[0]
        sports_data[date_str] = {
            'hours': row[1],
            'activities': row[2].split(',') if row[2] else []
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
            day_data = sports_data.get(date_str, {'hours': 0, 'activities': []})
            
            if is_future:
                intensity = 0
            else:
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
                'week': week_number,
                'gridColumn': week_number,
                'hours': day_data['hours'],
                'intensity': intensity,
                'activities': day_data['activities'],
                'isToday': current_date == today,
                'isWeekend': current_date.weekday() >= 5,
                'isFuture': is_future
            })
        
        current_date += timedelta(days=1)
    
    return calendar_data 