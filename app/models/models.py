# -*- coding: utf-8 -*-
from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


user_skills_table = db.Table(
    'user_skills',
    db.Column('id',         db.Integer, primary_key=True, autoincrement=True),
    db.Column('user_id',    db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('skill_id',   db.Integer, db.ForeignKey('skills.id'), nullable=False),
    db.Column('skill_type', db.String(10), nullable=False),
    db.Column('level',      db.Integer, default=3),
)

request_skills_table = db.Table(
    'request_skills',
    db.Column('request_id', db.Integer, db.ForeignKey('mentorship_requests.id'), primary_key=True),
    db.Column('skill_id',   db.Integer, db.ForeignKey('skills.id'), primary_key=True),
)


class FieldOfStudy(db.Model):
    __tablename__ = 'fields_of_study'
    id    = db.Column(db.Integer, primary_key=True)
    code  = db.Column(db.String(20),  nullable=False, unique=True)
    label = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='field', lazy=True)


class Skill(db.Model):
    __tablename__ = 'skills'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(150), nullable=False, unique=True)
    category = db.Column(db.String(100))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    first_name    = db.Column(db.String(100), nullable=False)
    last_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(255), nullable=False, unique=True)
    phone         = db.Column(db.String(20),  nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    field_id      = db.Column(db.Integer, db.ForeignKey('fields_of_study.id'))
    study_level   = db.Column(db.String(5), nullable=False, default='L1')
    bio           = db.Column(db.Text)
    photo_url     = db.Column(db.String(500))
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    availabilities      = db.relationship('UserAvailability',  backref='user',   lazy=True, cascade='all,delete-orphan')
    mentorship_requests = db.relationship('MentorshipRequest', backref='author', lazy=True, cascade='all,delete-orphan')
    notifications       = db.relationship('Notification',      backref='user',   lazy=True, cascade='all,delete-orphan')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_strengths(self):
        rows = db.session.execute(
            user_skills_table.select().where(
                (user_skills_table.c.user_id == self.id) &
                (user_skills_table.c.skill_type == 'strength')
            )
        ).fetchall()
        ids = [r.skill_id for r in rows]
        return [] if not ids else Skill.query.filter(Skill.id.in_(ids)).all()

    def get_weaknesses(self):
        rows = db.session.execute(
            user_skills_table.select().where(
                (user_skills_table.c.user_id == self.id) &
                (user_skills_table.c.skill_type == 'weakness')
            )
        ).fetchall()
        ids = [r.skill_id for r in rows]
        return [] if not ids else Skill.query.filter(Skill.id.in_(ids)).all()


class UserAvailability(db.Model):
    __tablename__ = 'user_availabilities'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time  = db.Column(db.Time, nullable=False)
    end_time    = db.Column(db.Time, nullable=False)
    DAY_LABELS  = ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']

    @property
    def day_label(self):
        return self.DAY_LABELS[self.day_of_week]


class MentorshipRequest(db.Model):
    __tablename__ = 'mentorship_requests'
    id           = db.Column(db.Integer, primary_key=True)
    author_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_type = db.Column(db.String(10), nullable=False)
    title        = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text)
    format       = db.Column(db.String(10), nullable=False, default='both')
    status       = db.Column(db.String(10), nullable=False, default='open')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    skills         = db.relationship('Skill', secondary=request_skills_table, lazy='subquery')
    availabilities = db.relationship('RequestAvailability', backref='request', lazy=True, cascade='all,delete-orphan')


class RequestAvailability(db.Model):
    __tablename__ = 'request_availabilities'
    id          = db.Column(db.Integer, primary_key=True)
    request_id  = db.Column(db.Integer, db.ForeignKey('mentorship_requests.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time  = db.Column(db.Time, nullable=False)
    end_time    = db.Column(db.Time, nullable=False)


class MatchingResult(db.Model):
    __tablename__ = 'matching_results'
    id             = db.Column(db.Integer, primary_key=True)
    mentor_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentee_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score          = db.Column(db.Float, nullable=False)
    skill_score    = db.Column(db.Float)
    schedule_score = db.Column(db.Float)
    field_score    = db.Column(db.Float)
    status         = db.Column(db.String(10), nullable=False, default='pending')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    mentor = db.relationship('User', foreign_keys=[mentor_id])
    mentee = db.relationship('User', foreign_keys=[mentee_id])
    __table_args__ = (db.UniqueConstraint('mentor_id', 'mentee_id'),)


class Conversation(db.Model):
    __tablename__ = 'conversations'
    id         = db.Column(db.Integer, primary_key=True)
    user1_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user1    = db.relationship('User', foreign_keys=[user1_id])
    user2    = db.relationship('User', foreign_keys=[user2_id])
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all,delete-orphan')
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id'),)

    def other_user(self, current_user_id):
        return self.user2 if self.user1_id == current_user_id else self.user1

    def last_message(self):
        return Message.query.filter_by(conversation_id=self.id).order_by(Message.sent_at.desc()).first()

    def unread_count(self, user_id):
        return Message.query.filter(
            Message.conversation_id == self.id,
            Message.is_read == False,
            Message.sender_id != user_id
        ).count()


class Message(db.Model):
    __tablename__ = 'messages'
    id              = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content         = db.Column(db.Text, nullable=False)
    is_read         = db.Column(db.Boolean, nullable=False, default=False)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id])


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type       = db.Column(db.String(50), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
