from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
from .logic import init_db, get_budget_data, get_calendar_data, add_budget_entry, get_today_entries

# Créer le blueprint
budget_bp = Blueprint('budget', __name__,
                      template_folder='templates',
                      static_folder='static')

# ✅ Middleware pour exiger l'authentification
@budget_bp.before_request
def require_login():
    allowed_routes = ['budget.favicon']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('auth.login'))  # Nom de l’endpoint du login

# ========== Routes principales ==========
@budget_bp.route('/')
def budget_index():
    return render_template('budget/index.html')

# ========== API Routes ==========
@budget_bp.route('/api/budget-data')
def get_budget_data_route():
    data = get_budget_data()
    return jsonify(data)

@budget_bp.route('/api/calendar-data')
def get_calendar_data_route():
    data = get_calendar_data()
    return jsonify(data)

@budget_bp.route('/api/budget-entries', methods=['POST'])
def add_budget_entry_route():
    data = request.json
    result = add_budget_entry(data)
    return jsonify(result)

@budget_bp.route('/api/debug-today')
def debug_today_route():
    data = get_today_entries()
    return jsonify(data)

@budget_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(budget_bp.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
