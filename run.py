# -*- coding: utf-8 -*-
"""
Lancement en local uniquement.
Sur Render, utiliser wsgi.py via gunicorn.
"""
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
