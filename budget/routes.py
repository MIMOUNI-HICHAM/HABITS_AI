from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
from .logic import (
    get_budget_data,
    get_calendar_data,
    add_budget_entry,
    get_today_entries
)

# Create blueprint
budget_bp = Blueprint('budget', __name__,
                      template_folder='templates',
                      static_folder='static')

# Middleware to require authentication
@budget_bp.before_request
def require_login():
    allowed_routes = ['budget.favicon']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('auth.login'))

# ========== Main Routes ==========
@budget_bp.route('/')
def budget_index():
    return render_template('budget/index.html')

# ========== API Routes ==========
@budget_bp.route('/api/budget-data', methods=['GET'])
def get_data():
    """Get budget data for dashboard."""
    try:
        data = get_budget_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budget_bp.route('/api/calendar-data')
def get_calendar():
    """Get budget calendar data."""
    try:
        calendar_data = get_calendar_data()
        return jsonify({
            'calendarData': calendar_data
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_calendar route: {str(e)}")
        return jsonify([])

@budget_bp.route('/api/budget-entries', methods=['POST'])
def add_budget_entry_route():
    try:
        data = request.json
        result = add_budget_entry(data)
        if 'error' in result:
            return jsonify(result), 401
        return jsonify({'success': True, 'message': 'Budget entry added successfully'})
    except Exception as e:
        current_app.logger.error(f"Error in add_budget_entry_route: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@budget_bp.route('/api/budget-today', methods=['GET'])
def get_today():
    """Get today's budget entries."""
    try:
        data = get_today_entries()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budget_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(budget_bp.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
