from flask import Flask, render_template, request, redirect, url_for
import requests
import time
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('api_monitor.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database (create table if it doesn't exist)
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            response_time REAL NOT NULL,
            status_code INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call init_db when the app starts
init_db()

@app.route('/', methods=['GET'])
def index():
    # Fetch all past results from the database
    conn = get_db_connection()
    tests = conn.execute('SELECT * FROM api_tests ORDER BY timestamp DESC').fetchall()
    conn.close()
    return render_template('index.html', tests=tests)

@app.route('/check', methods=['POST'])
def check_api():
    url = request.form['url']
    if not url:
        return redirect(url_for('index'))  # Redirect if no URL provided
    
    try:
        # Send GET request and measure time
        start_time = time.time()
        response = requests.get(url, timeout=10)  # 10-second timeout
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        status_code = response.status_code
        message = "Success" if status_code == 200 else f"Error: {response.reason}"
        
        # Store in database
        conn = get_db_connection()
        conn.execute('INSERT INTO api_tests (url, response_time, status_code, timestamp) VALUES (?, ?, ?, ?)',
                     (url, response_time, status_code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
    except requests.exceptions.RequestException as e:
        # Handle errors (e.g., network issues, invalid URL)
        response_time = 0.0
        status_code = 0
        message = f"Error: {str(e)}"
        
        # Still store the failed attempt
        conn = get_db_connection()
        conn.execute('INSERT INTO api_tests (url, response_time, status_code, timestamp) VALUES (?, ?, ?, ?)',
                     (url, response_time, status_code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    
    # Redirect back to index to show updated results
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)