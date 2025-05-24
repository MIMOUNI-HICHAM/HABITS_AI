import os
from dotenv import load_dotenv

load_dotenv()

# MySQL Database Configuration
# TODO: Update these values after installing MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # XAMPP default has no password for root
    'database': 'central',
    'port': 3306
}

def get_db_config():
    """Get database configuration from environment variables or use defaults."""
    return {
        'host': os.getenv('DB_HOST', MYSQL_CONFIG['host']),
        'user': os.getenv('DB_USER', MYSQL_CONFIG['user']),
        'password': os.getenv('DB_PASSWORD', MYSQL_CONFIG['password']),
        'database': os.getenv('DB_NAME', MYSQL_CONFIG['database']),
        'port': int(os.getenv('DB_PORT', MYSQL_CONFIG['port']))
    }

def get_db_connection_string():
    config = get_db_config()
    return f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}" 