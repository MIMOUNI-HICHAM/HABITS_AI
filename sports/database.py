import sqlite3
from config import DATABASE

def init_db():
    """Initialize the database with required tables."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sports_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                duration REAL,
                activity TEXT,
                location TEXT
            )
        ''')
        conn.commit()

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DATABASE)

def execute_query(query, params=()):
    """Execute a database query and return results."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()

def execute_update(query, params=()):
    """Execute a database update and commit changes."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit() 