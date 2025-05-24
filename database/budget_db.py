import mysql.connector
from mysql.connector import Error
from database.connection import get_connection

def get_budget_entries(user_id, start_date=None, end_date=None):
    """Get budget entries for a user within a date range."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            query = 'SELECT * FROM budget_entries WHERE user_id = %s'
            params = [user_id]
            
            if start_date and end_date:
                query += ' AND date BETWEEN %s AND %s'
                params.extend([start_date, end_date])
            
            query += ' ORDER BY date DESC'
            c.execute(query, params)
            return c.fetchall()
    except Error as e:
        print(f"Error getting budget entries: {e}")
        return []

def add_budget_entry(user_id, date, amount, category, description):
    """Add a new budget entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO budget_entries (user_id, date, amount, category, description)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, date, amount, category, description))
            conn.commit()
            return c.lastrowid
    except Error as e:
        print(f"Error adding budget entry: {e}")
        return None

def update_budget_entry(entry_id, amount, category, description):
    """Update an existing budget entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE budget_entries 
                SET amount = %s, category = %s, description = %s
                WHERE id = %s
            ''', (amount, category, description, entry_id))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error updating budget entry: {e}")
        return False

def delete_budget_entry(entry_id):
    """Delete a budget entry."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM budget_entries WHERE id = %s', (entry_id,))
            conn.commit()
            return c.rowcount > 0
    except Error as e:
        print(f"Error deleting budget entry: {e}")
        return False 