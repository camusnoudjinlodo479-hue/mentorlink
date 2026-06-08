# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.models import (
    MentorshipRequest, MatchingResult, Notification,
    Message, Conversation, User
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Stats reelles depuis la BDD
    nb_users    = User.query.filter_by(is_active=True).count()
    nb_sessions = MatchingResult.query.filter_by(status='accepted').count()
    nb_filieres = 5

    # Mentors = utilisateurs qui ont au moins un point fort
    from app.models.models import user_skills_table
    mentor_ids = db.session.execute(
        user_skills_table.select()
        .where(user_skills_table.c.skill_type == 'strength')
        .distinct()
    ).fetchall()
    mentor_id_list = list({r.user_id for r in mentor_ids})
    nb_mentors = len(mentor_id_list)
    mentors = User.query.filter(
        User.id.in_(mentor_id_list),
        User.is_active == True
    ).limit(8).all()

    return render_template('main/landing.html',
        nb_users=nb_users,
        nb_mentors=nb_mentors,
        nb_sessions=nb_sessions,
        nb_filieres=nb_filieres,
        mentors=mentors,
    )

@main_bp.route('/dashboard')
@login_required
def dashboard():
    recent_requests = MentorshipRequest.query.filter_by(status='open')\
        .order_by(MentorshipRequest.created_at.desc()).limit(5).all()

    my_matches = MatchingResult.query.filter(
        (MatchingResult.mentee_id == current_user.id) |
        (MatchingResult.mentor_id == current_user.id)
    ).order_by(MatchingResult.score.desc()).limit(5).all()

    my_conv_ids = db.session.query(Conversation.id).filter(
        (Conversation.user1_id == current_user.id) |
        (Conversation.user2_id == current_user.id)
    ).subquery()

    unread_messages = Message.query.filter(
        Message.conversation_id.in_(my_conv_ids),
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()

    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template('main/dashboard.html',
        recent_requests=recent_requests,
        my_matches=my_matches,
        unread_messages=unread_messages,
        notifications=notifications
    )
