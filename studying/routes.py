from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
from .logic import init_db, get_study_data, add_study_session, get_debug_today, get_calendar_data

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

# ✅ Initialise la base de données une seule fois
if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'studying.db')):
    init_db()

# ========== API Routes ==========
@studying_bp.route('/api/study-data')
def get_study_data_route():
    data = get_study_data()
    return jsonify(data)

@studying_bp.route('/api/study-sessions', methods=['POST'])
def add_study_session_route():
    data = request.json
    add_study_session(data)
    return jsonify({'message': 'Study session added successfully'})

@studying_bp.route('/api/debug-today')
def debug_today_route():
    data = get_debug_today()
    return jsonify(data)

@studying_bp.route('/api/calendar-data')
def get_calendar():
    return jsonify({
        'calendarData': get_calendar_data()
    })

# ========== Main Page ==========
@studying_bp.route('/')
def index():
    return render_template('studying/index.html')
