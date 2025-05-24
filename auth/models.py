import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_connection

class User:
    def __init__(self, id=None, username=None, password=None):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        try:
            with get_connection() as conn:
                c = conn.cursor(dictionary=True)
                c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                user_data = c.fetchone()
                if user_data:
                    return User(id=user_data['id'], username=user_data['username'], password=user_data['password'])
        except Error as e:
            print(f"Error getting user by id: {e}")
        return None

    @staticmethod
    def get_by_username(username):
        try:
            with get_connection() as conn:
                c = conn.cursor(dictionary=True)
                c.execute('SELECT * FROM users WHERE username = %s', (username,))
                user_data = c.fetchone()
                if user_data:
                    return User(id=user_data['id'], username=user_data['username'], password=user_data['password'])
        except Error as e:
            print(f"Error getting user by username: {e}")
        return None

    def save(self):
        try:
            with get_connection() as conn:
                c = conn.cursor()
                hashed_password = generate_password_hash(self.password)
                if self.id is None:
                    c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                              (self.username, hashed_password))
                    self.id = c.lastrowid
                else:
                    c.execute('UPDATE users SET username = %s, password = %s WHERE id = %s',
                              (self.username, hashed_password, self.id))
                conn.commit()
        except Error as e:
            print(f"Error saving user: {e}")

    def check_password(self, password):
        return check_password_hash(self.password, password)

def get_user_by_username(username):
    """Get a user by username."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute('SELECT * FROM users WHERE username = %s', (username,))
            return c.fetchone()
    except Error as e:
        print(f"Error getting user: {e}")
        return None

def create_user(username, password):
    """Create a new user."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            hashed_password = generate_password_hash(password)
            c.execute('INSERT INTO users (username, password) VALUES (%s, %s)',
                     (username, hashed_password))
            conn.commit()
            return c.lastrowid
    except Error as e:
        print(f"Error creating user: {e}")
        return None

def verify_password(username, password):
    """Verify a user's password."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute('SELECT password FROM users WHERE username = %s', (username,))
            user = c.fetchone()
            if user and check_password_hash(user['password'], password):
                return True
            return False
    except Error as e:
        print(f"Error verifying password: {e}")
        return False

def get_user_by_id(user_id):
    """Get a user by ID."""
    try:
        with get_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            return c.fetchone()
    except Error as e:
        print(f"Error getting user: {e}")
        return None

def update_user_password(user_id, new_password):
    """Update a user's password."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            hashed_password = generate_password_hash(new_password)
            c.execute('UPDATE users SET password = %s WHERE id = %s',
                     (hashed_password, user_id))
            conn.commit()
            return True
    except Error as e:
        print(f"Error updating password: {e}")
        return False

def seed_data():
    """Seed the authentication database with the default user."""
    with get_connection() as conn:
        c = conn.cursor()
        # Check if hicham user exists
        c.execute('SELECT * FROM users WHERE username = %s', ('hicham',))
        if not c.fetchone():
            # Create hicham user with password 12345678
            user = create_user('hicham', '12345678')
            print("✅ Default user 'hicham' created with password '12345678'")

# Initialize the database and seed data when the module is imported
seed_data() 