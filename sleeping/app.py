from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
from logic import (
    init_db, get_sleep_data, add_sleep_session, 
    get_today_sessions, get_calendar_data
)

app = Flask(__name__)

# Initialize the database only if it doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sleeping.db')):
    init_db()

# ========== API Routes ==========
@app.route('/api/sleep-data')
def get_sleep_data_route():
    data = get_sleep_data()
    return jsonify(data)

@app.route('/api/sleep-sessions', methods=['POST'])
def add_sleep_session_route():
    data = request.json
    add_sleep_session(data)
    return jsonify({'message': 'Sleep session added successfully'})

@app.route('/api/debug-today')
def debug_today_route():
    return jsonify(get_today_sessions())

@app.route('/api/calendar-data')
def api_calendar_data_route():
    return jsonify(get_calendar_data())

# ========== Main Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sleeping')
def sleeping():
    return render_template('sleeping.html')

if __name__ == '__main__':
    app.run(debug=True) 