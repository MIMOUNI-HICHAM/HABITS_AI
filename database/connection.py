import mysql.connector
from mysql.connector import Error
import logging
from .config import get_db_config

# Configure logging
logger = logging.getLogger(__name__)

def get_connection():
    """Get a MySQL database connection."""
    config = get_db_config()
    logger.debug(f"Attempting to connect to database: {config['database']} on {config['host']}:{config['port']}")
    try:
        connection = mysql.connector.connect(**config)
        logger.debug("Successfully connected to database")
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}", exc_info=True)
        if e.errno == 1049:  # Unknown database
            logger.error(f"Database '{config['database']}' does not exist")
        elif e.errno == 1045:  # Access denied
            logger.error(f"Access denied for user '{config['user']}'")
        elif e.errno == 2003:  # Can't connect to server
            logger.error(f"Could not connect to MySQL server at {config['host']}:{config['port']}")
        raise

def execute_query(query, params=()):
    """Execute a database query and return results."""
    try:
        logger.debug(f"Executing query: {query} with params: {params}")
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Query returned {len(results)} results")
            return results
    except Error as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        raise

def execute_update(query, params=()):
    """Execute a database update and commit changes."""
    try:
        logger.debug(f"Executing update: {query} with params: {params}")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            logger.debug("Update executed successfully")
    except Error as e:
        logger.error(f"Error executing update: {e}", exc_info=True)
        raise 