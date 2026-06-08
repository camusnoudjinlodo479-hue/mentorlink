# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.models import (
    MentorshipRequest, RequestAvailability, Skill,
    MatchingResult, Notification, request_skills_table
)
from app.utils.matching import generate_matches_for_mentee
from datetime import time as dtime

matching_bp = Blueprint('matching', __name__)


@matching_bp.route('/')
@login_required
def index():
    q        = request.args.get('q', '')
    req_type = request.args.get('type', '')
    skill_id = request.args.get('skill_id')
    skills   = Skill.query.order_by(Skill.name).all()

    query = MentorshipRequest.query.filter_by(status='open')
    if req_type in ('offer', 'demand'):
        query = query.filter_by(request_type=req_type)
    if skill_id:
        query = query.join(MentorshipRequest.skills).filter(Skill.id == int(skill_id))
    if q:
        # SQLite compatible: use lower() + like instead of ilike
        query = query.filter(MentorshipRequest.title.like(f'%{q}%'))

    requests_list = query.order_by(MentorshipRequest.created_at.desc()).all()
    return render_template('matching/index.html', requests=requests_list,
                           skills=skills, q=q, req_type=req_type, skill_id=skill_id)


@matching_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    skills = Skill.query.order_by(Skill.category, Skill.name).all()

    if request.method == 'POST':
        req_type    = request.form.get('request_type')
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        fmt         = request.form.get('format', 'both')
        skill_ids   = request.form.getlist('skills')
        days        = request.form.getlist('avail_day')
        starts      = request.form.getlist('avail_start')
        ends        = request.form.getlist('avail_end')

        if not title or not req_type:
            flash("Le titre et le type sont obligatoires.", 'danger')
            return render_template('matching/create.html', skills=skills)

        mr = MentorshipRequest(
            author_id=current_user.id, request_type=req_type,
            title=title, description=description, format=fmt,
        )
        db.session.add(mr)
        db.session.flush()

        for sid in skill_ids:
            db.session.execute(request_skills_table.insert().values(
                request_id=mr.id, skill_id=int(sid)
            ))

        for d, s, e in zip(days, starts, ends):
            if d and s and e:
                sh, sm = map(int, s.split(':'))
                eh, em = map(int, e.split(':'))
                db.session.add(RequestAvailability(
                    request_id=mr.id, day_of_week=int(d),
                    start_time=dtime(sh, sm), end_time=dtime(eh, em),
                ))

        db.session.commit()
        flash("Votre annonce a ete publiee.", 'success')
        return redirect(url_for('matching.index'))

    return render_template('matching/create.html', skills=skills)


@matching_bp.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    mr = db.session.get(MentorshipRequest, request_id)
    if not mr:
        flash("Annonce introuvable.", 'danger')
        return redirect(url_for('matching.index'))
    return render_template('matching/view_request.html', mr=mr)


@matching_bp.route('/my-requests')
@login_required
def my_requests():
    my = MentorshipRequest.query.filter_by(author_id=current_user.id)\
                                .order_by(MentorshipRequest.created_at.desc()).all()
    return render_template('matching/my_requests.html', requests=my)


@matching_bp.route('/find-mentors')
@login_required
def find_mentors():
    results = generate_matches_for_mentee(current_user, top_n=10)
    return render_template('matching/results.html', results=results)


@matching_bp.route('/match/<int:match_id>/respond', methods=['POST'])
@login_required
def respond_match(match_id):
    match = db.session.get(MatchingResult, match_id)
    if not match:
        return redirect(url_for('matching.find_mentors'))

    action = request.form.get('action')
    if match.mentee_id != current_user.id and match.mentor_id != current_user.id:
        flash("Action non autorisee.", 'danger')
        return redirect(url_for('matching.find_mentors'))

    if action in ('accepted', 'rejected'):
        match.status = action
        other_id = match.mentor_id if match.mentee_id == current_user.id else match.mentee_id
        msg = f"{current_user.full_name} a {'accepte' if action == 'accepted' else 'refuse'} votre proposition."
        db.session.add(Notification(user_id=other_id, type='match', content=msg))
        db.session.commit()

    return redirect(url_for('matching.find_mentors'))
