# -*- coding: utf-8 -*-
import os
from app import create_app, db
from flask_socketio import SocketIO

app = create_app()

# Fix pour Render : postgres:// → postgresql://
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
