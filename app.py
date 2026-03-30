from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import time
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'smart_queue_secret_2024'

DB_PATH = 'database.db'
AVG_SERVICE_TIME = 8  # minutes per person

# ─── Database Setup ────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                service TEXT DEFAULT 'General',
                status TEXT DEFAULT 'waiting',
                joined_at REAL NOT NULL,
                served_at REAL,
                position INTEGER
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        db.execute("INSERT OR IGNORE INTO settings VALUES ('avg_service_time', '8')")
        db.execute("INSERT OR IGNORE INTO settings VALUES ('counter_open', '1')")
        db.commit()

def generate_token():
    prefix = random.choice(['A', 'B', 'C'])
    number = random.randint(100, 999)
    return f"{prefix}{number}"

def get_avg_service_time():
    with get_db() as db:
        row = db.execute("SELECT value FROM settings WHERE key='avg_service_time'").fetchone()
        return int(row['value']) if row else AVG_SERVICE_TIME

def recalculate_positions():
    with get_db() as db:
        waiting = db.execute(
            "SELECT id FROM queue WHERE status='waiting' ORDER BY joined_at ASC"
        ).fetchall()
        for i, row in enumerate(waiting, 1):
            db.execute("UPDATE queue SET position=? WHERE id=?", (i, row['id']))
        db.commit()

def get_queue_stats():
    with get_db() as db:
        total_waiting = db.execute("SELECT COUNT(*) as c FROM queue WHERE status='waiting'").fetchone()['c']
        total_served_today = db.execute(
            "SELECT COUNT(*) as c FROM queue WHERE status='served' AND served_at > ?",
            (time.time() - 86400,)
        ).fetchone()['c']

        served_times = db.execute(
            "SELECT joined_at, served_at FROM queue WHERE status='served' AND served_at IS NOT NULL ORDER BY served_at DESC LIMIT 10"
        ).fetchall()

        if served_times:
            durations = [(r['served_at'] - r['joined_at']) / 60 for r in served_times]
            avg = sum(durations) / len(durations)
        else:
            avg = get_avg_service_time()

        return {
            'total_waiting': total_waiting,
            'total_served_today': total_served_today,
            'avg_service_time': round(avg, 1)
        }

# ─── User Routes ───────────────────────────────────────────────────

@app.route('/')
def index():
    stats = get_queue_stats()
    services = ['General', 'Billing', 'Support', 'Registration', 'Consultation']
    return render_template('index.html', stats=stats, services=services)

@app.route('/join', methods=['POST'])
def join_queue():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    service = request.form.get('service', 'General')

    if not name:
        return redirect(url_for('index'))

    token = generate_token()
    # Ensure unique token
    with get_db() as db:
        existing = db.execute("SELECT token FROM queue WHERE status='waiting'").fetchall()
        used_tokens = {r['token'] for r in existing}
        while token in used_tokens:
            token = generate_token()

        db.execute(
            "INSERT INTO queue (token, name, phone, service, joined_at) VALUES (?, ?, ?, ?, ?)",
            (token, name, phone, service, time.time())
        )
        db.commit()

    recalculate_positions()
    session['token'] = token
    return redirect(url_for('my_queue', token=token))

@app.route('/queue/<token>')
def my_queue(token):
    with get_db() as db:
        person = db.execute("SELECT * FROM queue WHERE token=?", (token,)).fetchone()
    if not person:
        return redirect(url_for('index'))

    avg_time = get_avg_service_time()
    wait_minutes = (person['position'] - 1) * avg_time if person['position'] else 0

    joined_dt = datetime.fromtimestamp(person['joined_at']).strftime('%I:%M %p')

    return render_template('queue.html',
        person=dict(person),
        wait_minutes=wait_minutes,
        joined_time=joined_dt,
        avg_service_time=avg_time
    )

@app.route('/status/<token>')
def status_api(token):
    with get_db() as db:
        person = db.execute("SELECT * FROM queue WHERE token=?", (token,)).fetchone()
    if not person:
        return jsonify({'error': 'Token not found'}), 404

    avg_time = get_avg_service_time()
    pos = person['position'] if person['position'] else 0
    wait_minutes = max(0, (pos - 1) * avg_time)

    return jsonify({
        'token': person['token'],
        'name': person['name'],
        'status': person['status'],
        'position': pos,
        'wait_minutes': wait_minutes,
        'service': person['service']
    })

@app.route('/leave/<token>', methods=['POST'])
def leave_queue(token):
    with get_db() as db:
        db.execute("UPDATE queue SET status='cancelled' WHERE token=? AND status='waiting'", (token,))
        db.commit()
    recalculate_positions()
    return redirect(url_for('index'))

# ─── Admin Routes ──────────────────────────────────────────────────

@app.route('/admin')
def admin():
    with get_db() as db:
        waiting = db.execute(
            "SELECT * FROM queue WHERE status='waiting' ORDER BY position ASC"
        ).fetchall()
        served_today = db.execute(
            "SELECT * FROM queue WHERE status='served' AND served_at > ? ORDER BY served_at DESC",
            (time.time() - 86400,)
        ).fetchall()

    stats = get_queue_stats()
    avg_time = get_avg_service_time()

    waiting_list = []
    for p in waiting:
        d = dict(p)
        d['joined_time'] = datetime.fromtimestamp(p['joined_at']).strftime('%I:%M %p')
        d['wait_minutes'] = max(0, (p['position'] - 1) * avg_time)
        waiting_list.append(d)

    served_list = []
    for p in served_today:
        d = dict(p)
        d['joined_time'] = datetime.fromtimestamp(p['joined_at']).strftime('%I:%M %p')
        if p['served_at']:
            d['served_time'] = datetime.fromtimestamp(p['served_at']).strftime('%I:%M %p')
            d['duration'] = round((p['served_at'] - p['joined_at']) / 60, 1)
        served_list.append(d)

    return render_template('admin.html',
        waiting=waiting_list,
        served_today=served_list,
        stats=stats,
        avg_time=avg_time
    )

@app.route('/admin/serve/<int:person_id>', methods=['POST'])
def serve_person(person_id):
    with get_db() as db:
        db.execute(
            "UPDATE queue SET status='served', served_at=? WHERE id=? AND status='waiting'",
            (time.time(), person_id)
        )
        db.commit()
    recalculate_positions()
    return redirect(url_for('admin'))

@app.route('/admin/remove/<int:person_id>', methods=['POST'])
def remove_person(person_id):
    with get_db() as db:
        db.execute("UPDATE queue SET status='cancelled' WHERE id=?", (person_id,))
        db.commit()
    recalculate_positions()
    return redirect(url_for('admin'))

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    avg_time = request.form.get('avg_service_time', '8')
    with get_db() as db:
        db.execute("UPDATE settings SET value=? WHERE key='avg_service_time'", (avg_time,))
        db.commit()
    return redirect(url_for('admin'))

@app.route('/api/queue')
def api_queue():
    with get_db() as db:
        waiting = db.execute(
            "SELECT token, name, service, position FROM queue WHERE status='waiting' ORDER BY position ASC"
        ).fetchall()
    stats = get_queue_stats()
    return jsonify({
        'queue': [dict(r) for r in waiting],
        'stats': stats
    })

# ─── Main ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
