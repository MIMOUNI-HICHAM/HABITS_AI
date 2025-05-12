from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app
import os
from .database import init_db, execute_update
from .logic import get_sports_data, get_calendar_data
from .config import DATABASE

sports_bp = Blueprint('sports', __name__,
                     template_folder='templates',  # Updated path
                     static_folder='static')

# ... (keep all your existing API routes) ...

@sports_bp.route('/')
def index():
    return render_template('sports/index.html')  # This will look in templates/sports/

# ... (rest of your routes) ...



@sports_bp.route('/api/sports-data')
def get_sports_data_route():
    try:
        data = get_sports_data()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error in get_sports_data_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@sports_bp.route('/api/sports-sessions', methods=['POST'])
def add_sports_session():
    data = request.json
    execute_update('''
        INSERT INTO sports_sessions (date, time, duration, activity, location)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['date'], data['time'], data['duration'], data['activity'], data['location']))
    return jsonify({'message': 'Sports session added successfully'})

@sports_bp.route('/api/calendar-data')
def get_calendar():
    return jsonify({'calendarData': get_calendar_data()})


@sports_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(sports_bp.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
