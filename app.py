# app.py — Application Flask simple
from flask import Flask, jsonify
import os

app = Flask(__name__)
VERSION = os.getenv('APP_VERSION', '1.0')

@app.route('/')
def home():
    return f'''
    <html>
      <head><title>Mon App CI/CD</title></head>
      <body style="font-family:Arial; margin:40px; background:#0D1117; color:white">
        <h1>🚀 Mon Application CI/CD</h1>
        <p>Version : <strong>{VERSION}</strong></p>
        <p>Déployée automatiquement via GitHub Actions + Docker 22</p>
        <p style="color:#56D364">✅ Pipeline exécuté avec succès</p>
      </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': VERSION})

@app.route('/formations')
def formations():
    data = [
        {'id': 1, 'titre': 'DevOps & CI/CD', 'duree': '40h'},
        {'id': 2, 'titre': 'Docker & Kubernetes', 'duree': '30h'},
        {'id': 3, 'titre': 'Python Flask', 'duree': '20h'},
    ]
    return jsonify({'formations': data, 'total': len(data)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
