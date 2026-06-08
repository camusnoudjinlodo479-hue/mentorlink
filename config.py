# -*- coding: utf-8 -*-
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ifri-mentorlink-secret-2526')

    # Sur Render : DATABASE_URL est fourni automatiquement (PostgreSQL)
    # En local   : SQLite par defaut
    _db_url = os.environ.get('DATABASE_URL', '')

    # Render fournit "postgres://..." mais SQLAlchemy veut "postgresql://..."
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or (
        'sqlite:///' + os.path.join(BASE_DIR, 'mentorlink.db')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION = timedelta(days=1)
    UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
