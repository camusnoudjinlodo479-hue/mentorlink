# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.models import User, FieldOfStudy, Skill, user_skills_table

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    fields = FieldOfStudy.query.all()
    skills = Skill.query.order_by(Skill.category, Skill.name).all()

    if request.method == 'POST':
        first_name  = request.form.get('first_name', '').strip()
        last_name   = request.form.get('last_name',  '').strip()
        email       = request.form.get('email', '').strip().lower()
        phone       = request.form.get('phone', '').strip()
        password    = request.form.get('password', '')
        confirm     = request.form.get('confirm_password', '')
        field_id    = request.form.get('field_id')
        study_level = request.form.get('study_level', 'L1')
        bio         = request.form.get('bio', '').strip()
        strengths   = request.form.getlist('strengths')
        weaknesses  = request.form.getlist('weaknesses')

        errors = []
        if not all([first_name, last_name, email, phone, password]):
            errors.append("Tous les champs obligatoires doivent etre remplis.")
        if password != confirm:
            errors.append("Les mots de passe ne correspondent pas.")
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caracteres.")
        if User.query.filter_by(email=email).first():
            errors.append("Cette adresse e-mail est deja utilisee.")
        if User.query.filter_by(phone=phone).first():
            errors.append("Ce numero de telephone est deja utilise.")

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', fields=fields, skills=skills)

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            first_name=first_name, last_name=last_name,
            email=email, phone=phone,
            password_hash=hashed,
            field_id=int(field_id) if field_id else None,
            study_level=study_level, bio=bio,
        )
        db.session.add(user)
        db.session.flush()

        for sid in strengths:
            db.session.execute(user_skills_table.insert().values(
                user_id=user.id, skill_id=int(sid), skill_type='strength', level=3
            ))
        for sid in weaknesses:
            db.session.execute(user_skills_table.insert().values(
                user_id=user.id, skill_id=int(sid), skill_type='weakness', level=1
            ))

        db.session.commit()
        flash('Compte cree avec succes ! Connectez-vous.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', fields=fields, skills=skills)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')
        remember   = request.form.get('remember') == 'on'

        user = User.query.filter(
            (User.email == identifier.lower()) | (User.phone == identifier)
        ).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Bienvenue, {user.first_name} !', 'success')
            return redirect(request.args.get('next') or url_for('main.dashboard'))

        flash('Identifiant ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous etes deconnecte.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email   = request.form.get('email', '').strip().lower()
        phone   = request.form.get('phone', '').strip()
        new_pw  = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')

        user = User.query.filter_by(email=email, phone=phone).first()
        if not user:
            flash("Aucun compte ne correspond a ces informations.", 'danger')
            return render_template('auth/reset_password.html')
        if new_pw != confirm:
            flash("Les mots de passe ne correspondent pas.", 'danger')
            return render_template('auth/reset_password.html')
        if len(new_pw) < 8:
            flash("Le mot de passe doit contenir au moins 8 caracteres.", 'danger')
            return render_template('auth/reset_password.html')

        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        flash("Mot de passe reinitialise avec succes.", 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')
