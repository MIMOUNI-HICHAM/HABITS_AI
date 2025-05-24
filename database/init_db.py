from mysql.connector import Error
from .connection import get_connection

def init_database():
    """Initialize the central database."""
    try:
        # Create database if it doesn't exist
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS central")
            conn.commit()
    except Error as e:
        print(f"Error creating database: {e}")
        raise

def init_tables():
    """Initialize all module tables."""
    try:
        # Import initialization functions
        from sports.logic import init_db as init_sports_db
        from sleeping.logic import init_db as init_sleeping_db
        from studying.logic import init_db as init_studying_db
        from budget.logic import init_db as init_budget_db
        
        # Initialize each module's database
        init_sports_db()
        init_sleeping_db()
        init_studying_db()
        init_budget_db()
    except Error as e:
        print(f"Error initializing tables: {e}")
        raise 