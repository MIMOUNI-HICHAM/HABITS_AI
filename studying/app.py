from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
from logic import init_db, get_study_data, add_study_session, get_debug_today, get_calendar_data

app = Flask(__name__)

# Initialize the database only if it doesn't exist
if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'studying.db')):
    init_db()

# ========== API Routes ==========
@app.route('/api/study-data')
def get_study_data_route():
    data = get_study_data()
    return jsonify(data)

@app.route('/api/study-sessions', methods=['POST'])
def add_study_session_route():
    data = request.json
    add_study_session(data)
    return jsonify({'message': 'Study session added successfully'})

@app.route('/api/debug-today')
def debug_today_route():
    data = get_debug_today()
    return jsonify(data)

@app.route('/api/calendar-data')
def get_calendar():
    return jsonify({
        'calendarData': get_calendar_data()
    })

# ========== Main Routes ==========
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

