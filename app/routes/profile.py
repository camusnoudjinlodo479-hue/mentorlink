# -*- coding: utf-8 -*-
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import time as dtime
from app import db
from app.models.models import User, FieldOfStudy, Skill, UserAvailability, user_skills_table

profile_bp = Blueprint('profile', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route('/<int:user_id>')
@login_required
def view(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Utilisateur introuvable.", 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('profile/view.html', user=user,
                           strengths=user.get_strengths(),
                           weaknesses=user.get_weaknesses())


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    fields = FieldOfStudy.query.all()
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    user   = current_user
    cur_strengths  = {s.id for s in user.get_strengths()}
    cur_weaknesses = {s.id for s in user.get_weaknesses()}

    if request.method == 'POST':
        user.first_name  = request.form.get('first_name', user.first_name).strip()
        user.last_name   = request.form.get('last_name',  user.last_name).strip()
        user.bio         = request.form.get('bio', '').strip()
        user.study_level = request.form.get('study_level', user.study_level)
        field_id         = request.form.get('field_id')
        user.field_id    = int(field_id) if field_id else None

        photo = request.files.get('photo')
        if photo and photo.filename and _allowed_file(photo.filename):
            filename  = secure_filename(f"user_{user.id}_{photo.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            photo.save(os.path.join(upload_dir, filename))
            user.photo_url = f'/static/uploads/{filename}'

        # Disponibilites
        UserAvailability.query.filter_by(user_id=user.id).delete()
        for d, s, e in zip(
            request.form.getlist('avail_day'),
            request.form.getlist('avail_start'),
            request.form.getlist('avail_end')
        ):
            if d and s and e:
                sh, sm = map(int, s.split(':'))
                eh, em = map(int, e.split(':'))
                db.session.add(UserAvailability(
                    user_id=user.id, day_of_week=int(d),
                    start_time=dtime(sh, sm), end_time=dtime(eh, em),
                ))

        # Competences
        db.session.execute(
            user_skills_table.delete().where(user_skills_table.c.user_id == user.id)
        )
        for sid in request.form.getlist('strengths'):
            db.session.execute(user_skills_table.insert().values(
                user_id=user.id, skill_id=int(sid), skill_type='strength', level=3
            ))
        for sid in request.form.getlist('weaknesses'):
            db.session.execute(user_skills_table.insert().values(
                user_id=user.id, skill_id=int(sid), skill_type='weakness', level=1
            ))

        db.session.commit()
        flash('Profil mis a jour avec succes.', 'success')
        return redirect(url_for('profile.view', user_id=user.id))

    return render_template('profile/edit.html', user=user, fields=fields, skills=skills,
                           cur_strengths=cur_strengths, cur_weaknesses=cur_weaknesses)
