from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import string
import random
import datetime
import os

app = Flask(__name__)

# --- Database Setup ---
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE urls (
                        original_url TEXT,
                        short_code TEXT UNIQUE,
                        created_at TEXT,
                        clicks INTEGER DEFAULT 0
                    )''')
        conn.commit()
        conn.close()

init_db()


# --- Generate Short Code ---
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# --- Home Page ---
@app.route('/')
def index():
    return render_template('index.html')


# --- Shorten URL ---
@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.form['original_url']
    short_code = generate_short_code()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check for duplicate URLs
    c.execute('SELECT short_code FROM urls WHERE original_url = ?', (original_url,))
    existing = c.fetchone()

    if existing:
        short_code = existing[0]
    else:
        c.execute('INSERT INTO urls (original_url, short_code, created_at) VALUES (?, ?, ?)',
                  (original_url, short_code, created_at))
        conn.commit()

    conn.close()

    short_url = request.host_url + short_code
    return render_template('index.html', short_url=short_url)


# --- Redirect Short URL ---
@app.route('/<short_code>')
def redirect_short(short_code):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
    result = c.fetchone()

    if result:
        original_url = result[0]
        c.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (short_code,))
        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        conn.close()
        return "Invalid short URL", 404


# --- Analytics Page ---
@app.route('/analytics')
def analytics():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT original_url, short_code, created_at, clicks FROM urls ORDER BY created_at DESC')
    data = c.fetchall()
    conn.close()

    return render_template('analytics.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
