from datetime import datetime, timedelta, date

def get_current_week_range():
    """Get the start and end dates of the current week."""
    today = datetime.combine(date.today(), datetime.min.time())
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')

def get_last_week_range():
    """Get the start and end dates of the last week."""
    today = datetime.combine(date.today(), datetime.min.time())
    start_of_week = today - timedelta(days=today.weekday())
    last_week_start = start_of_week - timedelta(days=7)
    last_week_end = start_of_week - timedelta(days=1)
    return last_week_start.strftime('%Y-%m-%d'), last_week_end.strftime('%Y-%m-%d')

def calculate_moving_average(data, window=7):
    """Calculate moving average for a list of (date, value) tuples."""
    if not data:
        return []
    
    data_list = [(d['date'], d['hours']) for d in data]
    result = []
    
    for i in range(len(data_list)):
        start_idx = max(0, i - window + 1)
        window_data = data_list[start_idx:i + 1]
        avg = sum(hours for _, hours in window_data) / len(window_data)
        result.append({'date': data_list[i][0], 'hours': round(avg, 2)})
    
    return result 