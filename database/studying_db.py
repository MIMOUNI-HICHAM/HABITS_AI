import mysql.connector
from mysql.connector import Error
from database.connection import get_connection

def get_studying_entries(user_id, start_date=None, end_date=None):
    """Get studying entries for a user within a date range."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            query = 'SELECT * FROM studying_entries WHERE user_id = %s'
            params = [user_id]
            
            if start_date and end_date:
                query += ' AND date BETWEEN %s AND %s'
                params.extend([start_date, end_date])
            
            query += ' ORDER BY date DESC'
            c.execute(query, params)
            return c.fetchall()
    except Error as e:
        print(f"Error getting studying entries: {e}")
        return []

def add_studying_entry(user_id, date, subject, hours, productivity, notes):
    """Add a new studying entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO studying_entries (user_id, date, subject, hours, productivity, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, date, subject, hours, productivity, notes))
            conn.commit()
            return c.lastrowid
    except Error as e:
        print(f"Error adding studying entry: {e}")
        return None

def update_studying_entry(entry_id, subject, hours, productivity, notes):
    """Update an existing studying entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE studying_entries 
                SET subject = %s, hours = %s, productivity = %s, notes = %s
                WHERE id = %s
            ''', (subject, hours, productivity, notes, entry_id))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error updating studying entry: {e}")
        return False

def delete_studying_entry(entry_id):
    """Delete a studying entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM studying_entries WHERE id = %s', (entry_id,))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error deleting studying entry: {e}")
        return False 