from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
from database import init_db
from logic import get_sports_data, get_calendar_data

app = Flask(__name__)

@app.route('/api/sports-data')
def get_sports_data_route():
    try:
        data = get_sports_data()
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error in get_sports_data_route: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/sports-sessions', methods=['POST'])
def add_sports_session():
    data = request.json
    from database import execute_update
    execute_update('''
        INSERT INTO sports_sessions (date, time, duration, activity, location)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['date'], data['time'], data['duration'], data['activity'], data['location']))
    return jsonify({'message': 'Sports session added successfully'})

@app.route('/api/calendar-data')
def get_calendar():
    return jsonify({
        'calendarData': get_calendar_data()
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 