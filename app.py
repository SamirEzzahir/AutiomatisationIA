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
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    cur.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"DB init failed: {e}")


@app.route('/')
def home():
    return f'''<!DOCTYPE html>
<html>
<head>
  <title>Mon App CI/CD</title>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #0D1117; color: white; padding: 40px; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #8b949e; font-size: 14px; margin-bottom: 24px; }}
    .badge {{ color: #56D364; }}
    h2 {{ margin-bottom: 12px; }}
    .add-row {{ display: flex; gap: 8px; margin-bottom: 24px; }}
    .add-row input {{
      flex: 1; padding: 10px 14px; border-radius: 6px;
      border: 1px solid #30363d; background: #161b22; color: white; font-size: 15px;
    }}
    .add-row input:focus {{ outline: none; border-color: #58a6ff; }}
    .add-row button {{
      padding: 10px 20px; border-radius: 6px; border: none;
      background: #238636; color: white; font-size: 15px; cursor: pointer;
    }}
    .add-row button:hover {{ background: #2ea043; }}
    ul {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
    li {{
      display: flex; align-items: center; gap: 12px;
      background: #161b22; border: 1px solid #30363d;
      border-radius: 8px; padding: 12px 16px;
    }} 
    li.done span {{ text-decoration: line-through; color: #8b949e; }}
    li span {{ flex: 1; font-size: 15px; }}
    input[type=checkbox] {{ width: 18px; height: 18px; cursor: pointer; accent-color: #56D364; }}
    .del-btn {{
      padding: 5px 12px; border-radius: 6px; border: none;
      background: #b91c1c; color: white; cursor: pointer; font-size: 13px;
    }}
    .del-btn:hover {{ background: #dc2626; }}
    .empty {{ color: #8b949e; font-style: italic; padding: 12px 0; }}
  </style>
</head>
<body style="width: 500px; margin: 0 auto;">
  <h1>🚀 Mon Application CI/CD</h1>
  <p class="meta">Version : <strong>{VERSION}</strong> &nbsp;|&nbsp; <span class="badge">✅ Pipeline OK</span></p>
 
  <h2>📋 Mes Tâches</h2>

  <div class="add-row">
    <input id="newTask" type="text" placeholder="Nouvelle tâche..." />
    <button onclick="addTask()">Ajouter</button>
  </div>

  <ul id="taskList"></ul>

  <script>
    async function loadTasks() {{
      const ul = document.getElementById('taskList');
      try {{
        const res = await fetch('/tasks');
        if (!res.ok) throw new Error(`HTTP ${{res.status}}`);
        const data = await res.json();
        ul.innerHTML = '';
        if (data.tasks.length === 0) {{
          ul.innerHTML = '<p class="empty">Aucune tâche pour le moment.</p>';
          return;
        }}
        data.tasks.forEach(t => ul.appendChild(makeItem(t)));
      }} catch (e) {{
        ul.innerHTML = `<p style="color:#f87171">❌ Erreur: ${{e.message}} — La base de données est-elle démarrée ?</p>`;
      }}
    }}

    function makeItem(t) {{
      const li = document.createElement('li');
      if (t.done) li.classList.add('done');

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = t.done;
      cb.onchange = () => toggleTask(t.id, cb.checked);

      const span = document.createElement('span');
      span.textContent = t.title;

      const btn = document.createElement('button');
      btn.className = 'del-btn';
      btn.textContent = 'Supprimer';
      btn.onclick = () => deleteTask(t.id);

      li.append(cb, span, btn);
      return li;
    }}

    async function addTask() {{
      const input = document.getElementById('newTask');
      const title = input.value.trim();
      if (!title) return;
      await fetch('/tasks', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ title }})
      }});
      input.value = '';
      loadTasks();
    }}

    async function toggleTask(id, done) {{
      await fetch(`/tasks/${{id}}`, {{
        method: 'PUT',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{ done }})
      }});
      loadTasks();
    }}

    async function deleteTask(id) {{
      await fetch(`/tasks/${{id}}`, {{ method: 'DELETE' }});
      loadTasks();
    }}

    document.getElementById('newTask').addEventListener('keydown', e => {{
      if (e.key === 'Enter') addTask();
    }});

    loadTasks();
  </script>
</body>
</html>'''


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
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    tasks = [dict(t) for t in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({'tasks': tasks, 'total': len(tasks)})


@app.route('/tasks', methods=['POST'])
def create_task():
    body = request.get_json()
    if not body or not body.get('title'):
        return jsonify({'error': 'title is required'}), 400
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        'INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *',
        (body['title'], body.get('done', False))
    )
    task = dict(cur.fetchone())
    cur.close()
    conn.close()
    return jsonify(task), 201


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    body = request.get_json()
    if not body:
        return jsonify({'error': 'body is required'}), 400
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        'UPDATE tasks SET title = COALESCE(%s, title), done = COALESCE(%s, done) WHERE id = %s RETURNING *',
        (body.get('title'), body.get('done'), task_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({'error': 'task not found'}), 404
    return jsonify(dict(row))


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM tasks WHERE id = %s RETURNING id', (task_id,))
    deleted = cur.fetchone()
    cur.close()
    conn.close()
    if not deleted:
        return jsonify({'error': 'task not found'}), 404
    return jsonify({'deleted': task_id})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
