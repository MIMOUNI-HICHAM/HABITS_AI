from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app, session, redirect, url_for
import os
import logging
from .logic import get_sports_data, get_calendar_data, init_db
from database.connection import get_connection
from datetime import datetime
import mysql.connector

# Configure logging
logger = logging.getLogger(__name__)

sports_bp = Blueprint('sports', __name__,
                      template_folder='templates',
                      static_folder='static')

# Remove automatic initialization
# init_db()  # This was causing issues

# ✅ Fonction exécutée AVANT chaque route
@sports_bp.before_request
def require_login():
    logger.debug(f"Checking authentication for route: {request.endpoint}")
    allowed_routes = ['sports.favicon', 'sports.init_database']  # Added init_database to allowed routes
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
        return redirect(url_for('auth.login'))  # 'auth.login' doit correspondre à ton endpoint de login

# ✅ Ta route index (PAS décorée avec before_request)
@sports_bp.route('/')
def index():
    logger.info("Rendering sports index page")
    return render_template('sports/index.html')

# ✅ Le reste de tes routes
@sports_bp.route('/api/sports-data')
def get_sports_data_route():
    try:
        logger.info("Fetching sports data for dashboard")
        data = get_sports_data()
        logger.debug(f"Successfully fetched sports data with {len(data.get('dailyData', []))} daily entries")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in get_sports_data_route: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sports_bp.route('/add_session', methods=['POST'])
def add_session():
    if 'user_id' not in session:
        logger.warning("Unauthenticated attempt to add sports session")
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.json
    logger.info(f"Adding new sports session: {data}")
    try:
        # Validate required fields
        required_fields = ['date', 'time', 'duration', 'activity']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate data types
        try:
            float(data['duration'])
        except (ValueError, TypeError):
            logger.error(f"Invalid duration value: {data['duration']}")
            return jsonify({'error': 'Duration must be a number'}), 400

        # Log the exact SQL parameters
        params = (
            session['user_id'],
            data['date'],
            data['time'],
            data['duration'],
            data['activity'],
            data.get('intensity', 'moderate'),
            data.get('notes', '')
        )
        logger.debug(f"SQL parameters: {params}")

        with get_connection() as conn:
            c = conn.cursor()
            try:
                c.execute('''
                    INSERT INTO sports_sessions (user_id, date, time, duration, activity, intensity, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', params)
                conn.commit()
                logger.info(f"Successfully added sports session for user {session['user_id']}")
                return jsonify({'message': 'Session added successfully'})
            except mysql.connector.Error as db_error:
                logger.error(f"Database error: {db_error}", exc_info=True)
                return jsonify({'error': f'Database error: {str(db_error)}'}), 500
    except Exception as e:
        logger.error(f"Error adding sports session: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@sports_bp.route('/api/calendar-data')
def get_calendar():
    try:
        logger.info("Fetching calendar data")
        calendar_data = get_calendar_data()
        logger.debug(f"Successfully fetched calendar data with {len(calendar_data)} entries")
        return jsonify({'calendarData': calendar_data})
    except Exception as e:
        logger.error(f"Error fetching calendar data: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sports_bp.route('/favicon.ico')
def favicon():
    logger.debug("Serving favicon")
    return send_from_directory(os.path.join(sports_bp.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@sports_bp.route('/init-database')
def init_database():
    """Initialize the database tables if they don't exist."""
    try:
        logger.info("Initializing database tables")
        init_db()
        logger.info("Database tables initialized successfully")
        return jsonify({'message': 'Database initialized successfully'})
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to initialize database', 'message': str(e)}), 500
