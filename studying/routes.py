from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
from .logic import get_study_data, add_study_session, get_today_sessions, get_calendar_data, get_common_topics

# Create blueprint
studying_bp = Blueprint('studying', __name__,
                        template_folder='templates',
                        static_folder='static')

# ✅ Middleware de protection : exécuter avant chaque route
@studying_bp.before_request
def require_login():
    allowed_routes = ['studying.favicon']  # Ajoute ici d'autres routes publiques si besoin
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('auth.login'))  # Redirige vers la page de login

# ========== API Routes ==========
@studying_bp.route('/api/study-data')
def get_study_data_route():
    data = get_study_data()
    return jsonify(data)

@studying_bp.route('/api/study-sessions', methods=['POST'])
def add_study_session_route():
    try:
        data = request.json
        result = add_study_session(data)
        if 'error' in result:
            return jsonify(result), 401
        return jsonify({'success': True, 'message': 'Study session added successfully'})
    except Exception as e:
        current_app.logger.error(f"Error in add_study_session_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@studying_bp.route('/api/today-study-sessions')
def today_sessions():
    return jsonify(get_today_sessions())

@studying_bp.route('/api/calendar-data')
def get_calendar():
    return jsonify({
        'calendarData': get_calendar_data()
    })

@studying_bp.route('/api/common-topics')
def get_common_topics_route():
    topics = get_common_topics()
    return jsonify(topics)

# ========== Main Page ==========
@studying_bp.route('/')
def index():
    return render_template('studying/index.html')
