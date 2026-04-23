# app.py — Application Flask simple
from flask import Flask, jsonify, request
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
VERSION = os.getenv('APP_VERSION', '1.0')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')

try:
    init_db()
except Exception:
    pass


@app.route('/')
def home():
    return f'''
    <html>
      <head><title>Mon App CI/CD</title></head>
      <body style="font-family:Arial; margin:40px; background:#0D1117; color:white">
        <h1>🚀 Mon Application CI/CD</h1>
        <p>Version : <strong>{VERSION}</strong></p>
        <p>Déployée automatiquement via GitHub Actions + Docker</p>
        <p style="color:#56D364">✅ Pipeline exécuté avec succès</p>
        <hr style="border-color:#333">
        <h2>📋 Tasks API</h2>
        <p>GET &nbsp;&nbsp;<code>/tasks</code> — liste toutes les tâches</p>
        <p>POST &nbsp;<code>/tasks</code> — créer une tâche (JSON: title)</p>
        <p>PUT &nbsp;&nbsp;<code>/tasks/&lt;id&gt;</code> — modifier une tâche</p>
        <p>DELETE <code>/tasks/&lt;id&gt;</code> — supprimer une tâche</p>
      </body>
    </html>
    '''


@app.route('/health')
def health():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
        db_status = 'ok'
    except Exception:
        db_status = 'error'
    return jsonify({'status': 'ok', 'version': VERSION, 'database': db_status})


@app.route('/formations')
def formations():
    data = [
        {'id': 1, 'titre': 'DevOps & CI/CD', 'duree': '40h'},
        {'id': 2, 'titre': 'Docker & Kubernetes', 'duree': '30h'},
        {'id': 3, 'titre': 'Python Flask', 'duree': '20h'},
    ]
    return jsonify({'formations': data, 'total': len(data)})


@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello depuis la v2 !', 'version': VERSION})


# ── Tasks CRUD ────────────────────────────────────────────────

@app.route('/tasks', methods=['GET'])
def list_tasks():
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM tasks ORDER BY created_at DESC')
            tasks = cur.fetchall()
    return jsonify({'tasks': [dict(t) for t in tasks], 'total': len(tasks)})


@app.route('/tasks', methods=['POST'])
def create_task():
    body = request.get_json()
    if not body or not body.get('title'):
        return jsonify({'error': 'title is required'}), 400
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *',
                (body['title'], body.get('done', False))
            )
            task = cur.fetchone()
    return jsonify(dict(task)), 201


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    body = request.get_json()
    if not body:
        return jsonify({'error': 'body is required'}), 400
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'UPDATE tasks SET title = COALESCE(%s, title), done = COALESCE(%s, done) WHERE id = %s RETURNING *',
                (body.get('title'), body.get('done'), task_id)
            )
            task = cur.fetchone()
    if not task:
        return jsonify({'error': 'task not found'}), 404
    return jsonify(dict(task))


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM tasks WHERE id = %s RETURNING id', (task_id,))
            deleted = cur.fetchone()
    if not deleted:
        return jsonify({'error': 'task not found'}), 404
    return jsonify({'deleted': task_id})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
