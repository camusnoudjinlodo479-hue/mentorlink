# -*- coding: utf-8 -*-
from app import db
from app.models.models import User, UserAvailability, MatchingResult, user_skills_table


def _get_skill_ids(user_id, skill_type):
    rows = db.session.execute(
        user_skills_table.select().where(
            (user_skills_table.c.user_id == user_id) &
            (user_skills_table.c.skill_type == skill_type)
        )
    ).fetchall()
    return {r.skill_id for r in rows}


def _time_overlap_minutes(s1, e1, s2, e2):
    from datetime import datetime, date
    base = date.today()
    overlap_start = max(datetime.combine(base, s1), datetime.combine(base, s2))
    overlap_end   = min(datetime.combine(base, e1), datetime.combine(base, e2))
    delta = (overlap_end - overlap_start).total_seconds() / 60
    return max(0.0, delta)


def _schedule_score(mentor_id, mentee_id):
    from datetime import datetime, date
    mentor_dispos = UserAvailability.query.filter_by(user_id=mentor_id).all()
    mentee_dispos = UserAvailability.query.filter_by(user_id=mentee_id).all()

    if not mentor_dispos or not mentee_dispos:
        return 0.0

    base = date.today()
    total = sum(
        (datetime.combine(base, d.end_time) - datetime.combine(base, d.start_time)).total_seconds() / 60
        for d in mentor_dispos
    )
    if total == 0:
        return 0.0

    overlap = 0.0
    for md in mentor_dispos:
        for td in mentee_dispos:
            if md.day_of_week == td.day_of_week:
                overlap += _time_overlap_minutes(md.start_time, md.end_time, td.start_time, td.end_time)

    return min(100.0, (overlap / total) * 100)


def _skill_score(mentor_id, mentee_id):
    mentor_strengths  = _get_skill_ids(mentor_id, 'strength')
    mentee_weaknesses = _get_skill_ids(mentee_id, 'weakness')
    if not mentee_weaknesses:
        return 0.0
    return (len(mentor_strengths & mentee_weaknesses) / len(mentee_weaknesses)) * 100


def _field_score(mentor, mentee):
    LEVEL_ORDER   = {'L1': 1, 'L2': 2, 'L3': 3, 'M1': 4, 'M2': 5}
    STEM_CLUSTERS = [{'IA', 'IM'}, {'GL', 'SE', 'SI'}]

    base = 20.0
    if mentor.field_id and mentee.field_id:
        if mentor.field_id == mentee.field_id:
            base = 100.0
        else:
            mc = mentor.field.code if mentor.field else ''
            tc = mentee.field.code if mentee.field else ''
            for cluster in STEM_CLUSTERS:
                if mc in cluster and tc in cluster:
                    base = 50.0
                    break

    if LEVEL_ORDER.get(mentor.study_level, 1) >= LEVEL_ORDER.get(mentee.study_level, 1):
        base = min(100.0, base + 20)

    return base


def compute_match_score(mentor, mentee):
    sk = _skill_score(mentor.id, mentee.id)
    sc = _schedule_score(mentor.id, mentee.id)
    fi = _field_score(mentor, mentee)
    return {
        'skill_score':    round(sk, 2),
        'schedule_score': round(sc, 2),
        'field_score':    round(fi, 2),
        'total':          round(0.50 * sk + 0.30 * sc + 0.20 * fi, 2),
    }


def generate_matches_for_mentee(mentee, top_n=10):
    candidates = User.query.filter(User.id != mentee.id, User.is_active == True).all()
    results = []

    for mentor in candidates:
        scores = compute_match_score(mentor, mentee)
        if scores['total'] < 10:
            continue

        existing = MatchingResult.query.filter_by(
            mentor_id=mentor.id, mentee_id=mentee.id
        ).first()

        if existing:
            existing.score          = scores['total']
            existing.skill_score    = scores['skill_score']
            existing.schedule_score = scores['schedule_score']
            existing.field_score    = scores['field_score']
            if existing.status != 'accepted':
                existing.status = 'pending'
        else:
            existing = MatchingResult(
                mentor_id=mentor.id, mentee_id=mentee.id,
                score=scores['total'], skill_score=scores['skill_score'],
                schedule_score=scores['schedule_score'], field_score=scores['field_score'],
            )
            db.session.add(existing)

        results.append(existing)

    db.session.commit()
    results.sort(key=lambda r: float(r.score), reverse=True)
    return results[:top_n]
