from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
from logic import (
    init_db, get_budget_data, get_calendar_data,
    add_budget_entry, get_today_entries
)

app = Flask(__name__)

# ========== API Routes ==========
@app.route('/api/budget-data')
def get_budget_data_route():
    data = get_budget_data()
    return jsonify(data)

@app.route('/api/calendar-data')
def get_calendar_data_route():
    data = get_calendar_data()
    return jsonify(data)

@app.route('/api/budget-entries', methods=['POST'])
def add_budget_entry_route():
    data = request.json
    result = add_budget_entry(data)
    return jsonify(result)

@app.route('/api/debug-today')
def debug_today_route():
    data = get_today_entries()
    return jsonify(data)

# ========== Main Routes ==========
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
