# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

db            = SQLAlchemy()
login_manager = LoginManager()
bcrypt        = Bcrypt()
socketio      = SocketIO()


def create_app(config_object='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')

    login_manager.login_view     = 'auth.login'
    login_manager.login_message  = 'Veuillez vous connecter.'
    login_manager.login_message_category = 'info'

    from app.routes.auth      import auth_bp
    from app.routes.profile   import profile_bp
    from app.routes.matching  import matching_bp
    from app.routes.messaging import messaging_bp
    from app.routes.main      import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(profile_bp,   url_prefix='/profile')
    app.register_blueprint(matching_bp,  url_prefix='/matching')
    app.register_blueprint(messaging_bp, url_prefix='/messaging')

    # Creer les tables et inserer les donnees de base
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Insere les donnees de base si la BDD est vide."""
    from app.models.models import FieldOfStudy, Skill

    if FieldOfStudy.query.count() == 0:
        fields = [
            FieldOfStudy(code='IA', label='Intelligence Artificielle'),
            FieldOfStudy(code='IM', label='Ingenierie Mathematique'),
            FieldOfStudy(code='GL', label='Genie Logiciel'),
            FieldOfStudy(code='SE', label='Systemes Embarques et IoT'),
            FieldOfStudy(code='SI', label='Systemes d Information'),
        ]
        db.session.add_all(fields)
        db.session.commit()

    if Skill.query.count() == 0:
        skills = [
            Skill(name='Algorithmique',           category='Informatique'),
            Skill(name='Python',                  category='Programmation'),
            Skill(name='JavaScript',              category='Programmation'),
            Skill(name='HTML/CSS',                category='Web'),
            Skill(name='SQL',                     category='Bases de donnees'),
            Skill(name='Bases de donnees',        category='Bases de donnees'),
            Skill(name='Mathematiques discretes', category='Mathematiques'),
            Skill(name='Algebre lineaire',        category='Mathematiques'),
            Skill(name='Probabilites',            category='Mathematiques'),
            Skill(name='Machine Learning',        category='IA'),
            Skill(name='Reseaux de neurones',     category='IA'),
            Skill(name='Systemes embarques',      category='Materiel'),
            Skill(name='IoT',                     category='Materiel'),
            Skill(name='Genie logiciel',          category='Methodes'),
            Skill(name='Gestion de projet',       category='Methodes'),
        ]
        db.session.add_all(skills)
        db.session.commit()
