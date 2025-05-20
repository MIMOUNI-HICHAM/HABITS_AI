import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PROJECT_ROOT, 'auth', 'auth.db')

def init_db():
    """Initialize the authentication database."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

class User:
    def __init__(self, id=None, username=None, password=None):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        """Get a user by their ID."""
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = c.fetchone()
            if user_data:
                return User(id=user_data[0], username=user_data[1], password=user_data[2])
        return None

    @staticmethod
    def get_by_username(username):
        """Get a user by their username."""
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_data = c.fetchone()
            if user_data:
                return User(id=user_data[0], username=user_data[1], password=user_data[2])
        return None

    def save(self):
        """Save the user to the database."""
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if self.id is None:
                # New user
                hashed_password = generate_password_hash(self.password)
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (self.username, hashed_password))
                self.id = c.lastrowid
            else:
                # Update existing user
                hashed_password = generate_password_hash(self.password)
                c.execute('UPDATE users SET username = ?, password = ? WHERE id = ?',
                         (self.username, hashed_password, self.id))
            conn.commit()

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password, password)

def seed_data():
    """Seed the authentication database with the default user."""
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Check if hicham user exists
        c.execute('SELECT * FROM users WHERE username = ?', ('hicham',))
        if not c.fetchone():
            # Create hicham user with password 12345678
            user = User(username='hicham', password='12345678')
            user.save()
            print("✅ Default user 'hicham' created with password '12345678'")

# Initialize the database and seed data when the module is imported
init_db()
seed_data() 