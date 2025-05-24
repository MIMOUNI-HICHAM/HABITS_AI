from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for, current_app
import os
from .logic import get_sleep_data, add_sleep_session, get_today_sessions, get_calendar_data, init_db

# Create blueprint
sleeping_bp = Blueprint('sleeping', __name__,
                        template_folder='templates',
                        static_folder='static')

def initialize_sleeping_db():
    """Initialize the sleeping database tables."""
    try:
        init_db()
        current_app.logger.info("Sleeping database initialized successfully")
    except Exception as e:
        current_app.logger.error(f"Failed to initialize sleeping database: {str(e)}")
        raise

# Middleware pour exiger l'authentification
@sleeping_bp.before_request
def require_login():
    allowed_routes = ['sleeping.favicon']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('auth.login'))

# ========== API Routes ==========
@sleeping_bp.route('/api/sleep-data')
def get_sleep_data_route():
    try:
        data = get_sleep_data()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error in get_sleep_data_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sleeping_bp.route('/api/sleep-sessions', methods=['POST'])
def add_sleep_session_route():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['date', 'hours', 'quality']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            
        result = add_sleep_session(data)
        if 'error' in result:
            return jsonify(result), 401
        return jsonify({'success': True, 'message': 'Sleep session added successfully'})
    except Exception as e:
        current_app.logger.error(f"Error in add_sleep_session_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sleeping_bp.route('/api/today-sleep-sessions')
def today_sessions():
    try:
        return jsonify(get_today_sessions())
    except Exception as e:
        current_app.logger.error(f"Error in today_sessions: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sleeping_bp.route('/api/calendar-data')
def api_calendar_data_route():
    try:
        calendar_data = get_calendar_data()
        if not calendar_data:
            return jsonify({'calendarData': []})
        return jsonify({'calendarData': calendar_data})
    except Exception as e:
        current_app.logger.error(f"Error in api_calendar_data_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# ========== Main Routes ==========
@sleeping_bp.route('/')
def index():
    return render_template('sleeping/index.html')

@sleeping_bp.route('/sleeping')
def sleeping():
    return render_template('sleeping/sleeping.html')

@sleeping_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(sleeping_bp.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
