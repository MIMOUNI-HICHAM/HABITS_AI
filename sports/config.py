import os

# Database configuration
DATABASE = os.path.join(os.path.dirname(__file__), 'sports.db')

# Weekly goal configuration
WEEKLY_GOAL = 10  # Weekly goal in hours

# Minimum duration for streak calculation
MIN_DURATION_PER_DAY = 0.5  # Minimum duration (30 minutes) required to count as an active day 