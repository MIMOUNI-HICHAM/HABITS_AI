from flask import Blueprint, render_template, request, jsonify, send_from_directory
import os
from .logic import init_db, get_sleep_data, add_sleep_session, get_today_sessions, get_calendar_data

# Create blueprint
sleeping_bp = Blueprint('sleeping', __name__,
                       template_folder='templates',
                       static_folder='static')

# Initialize the database only if it doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sleeping.db')):
    init_db()

# ========== API Routes ==========
@sleeping_bp.route('/api/sleep-data')
def get_sleep_data_route():
    data = get_sleep_data()
    return jsonify(data)

@sleeping_bp.route('/api/sleep-sessions', methods=['POST'])
def add_sleep_session_route():
    data = request.json
    add_sleep_session(data)
    return jsonify({'message': 'Sleep session added successfully'})

@sleeping_bp.route('/api/debug-today')
def debug_today_route():
    return jsonify(get_today_sessions())

@sleeping_bp.route('/api/calendar-data')
def api_calendar_data_route():
    return jsonify(get_calendar_data())

# ========== Main Routes ==========
@sleeping_bp.route('/')
def index():
    return render_template('sleeping/index.html')

@sleeping_bp.route('/sleeping')
def sleeping():
    return render_template('sleeping/sleeping.html') 