import mysql.connector
from mysql.connector import Error
from database.connection import get_connection

def get_sleep_entries(user_id, start_date=None, end_date=None):
    """Get sleep entries for a user within a date range."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            query = 'SELECT * FROM sleeping_entries WHERE user_id = %s'
            params = [user_id]
            
            if start_date and end_date:
                query += ' AND date BETWEEN %s AND %s'
                params.extend([start_date, end_date])
            
            query += ' ORDER BY date DESC'
            c.execute(query, params)
            return c.fetchall()
    except Error as e:
        print(f"Error getting sleep entries: {e}")
        return []

def add_sleep_entry(user_id, date, hours, quality, notes):
    """Add a new sleep entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO sleeping_entries (user_id, date, hours, quality, notes)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, date, hours, quality, notes))
            conn.commit()
            return c.lastrowid
    except Error as e:
        print(f"Error adding sleep entry: {e}")
        return None

def update_sleep_entry(entry_id, hours, quality, notes):
    """Update an existing sleep entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE sleeping_entries 
                SET hours = %s, quality = %s, notes = %s
                WHERE id = %s
            ''', (hours, quality, notes, entry_id))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error updating sleep entry: {e}")
        return False

def delete_sleep_entry(entry_id):
    """Delete a sleep entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM sleeping_entries WHERE id = %s', (entry_id,))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error deleting sleep entry: {e}")
        return False 