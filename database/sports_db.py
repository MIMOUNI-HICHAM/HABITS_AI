import mysql.connector
from mysql.connector import Error
from database.connection import get_connection

def get_sports_entries(user_id, start_date=None, end_date=None):
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            query = 'SELECT * FROM sports_entries WHERE user_id = %s'
            params = [user_id]
            if start_date and end_date:
                query += ' AND date BETWEEN %s AND %s'
                params.extend([start_date, end_date])
            query += ' ORDER BY date DESC'
            c.execute(query, params)
            return c.fetchall()
    except Error as e:
        print(f"Error getting sports entries: {e}")
        return []

def add_sports_entry(user_id, date, activity, duration, location):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO sports_entries (user_id, date, activity, duration, location)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, date, activity, duration, location))
            conn.commit()
            return c.lastrowid
    except Error as e:
        print(f"Error adding sports entry: {e}")
        return None

def update_sports_entry(entry_id, activity, duration, location):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE sports_entries 
                SET activity = %s, duration = %s, location = %s
                WHERE id = %s
            ''', (activity, duration, location, entry_id))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error updating sports entry: {e}")
        return False

def delete_sports_entry(entry_id):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM sports_entries WHERE id = %s', (entry_id,))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error deleting sports entry: {e}")
        return False 