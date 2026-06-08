# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models.models import Conversation, Message, User, Notification

messaging_bp = Blueprint('messaging', __name__)


@messaging_bp.route('/')
@login_required
def index():
    convs = Conversation.query.filter(
        (Conversation.user1_id == current_user.id) |
        (Conversation.user2_id == current_user.id)
    ).order_by(Conversation.created_at.desc()).all()
    return render_template('messaging/index.html', conversations=convs)


@messaging_bp.route('/with/<int:other_id>')
@login_required
def open_conversation(other_id):
    if other_id == current_user.id:
        flash("Vous ne pouvez pas vous envoyer un message.", 'warning')
        return redirect(url_for('messaging.index'))

    other = db.session.get(User, other_id)
    if not other:
        flash("Utilisateur introuvable.", 'danger')
        return redirect(url_for('messaging.index'))

    conv = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == other_id)) |
        ((Conversation.user1_id == other_id) & (Conversation.user2_id == current_user.id))
    ).first()

    if not conv:
        u1, u2 = sorted([current_user.id, other_id])
        conv = Conversation(user1_id=u1, user2_id=u2)
        db.session.add(conv)
        db.session.commit()

    for m in Message.query.filter(
        Message.conversation_id == conv.id,
        Message.is_read == False,
        Message.sender_id != current_user.id
    ).all():
        m.is_read = True
    db.session.commit()

    messages = Message.query.filter_by(conversation_id=conv.id)\
                            .order_by(Message.sent_at.asc()).all()
    return render_template('messaging/conversation.html',
                           conversation=conv, messages=messages, other=other)


@messaging_bp.route('/send/<int:conv_id>', methods=['POST'])
@login_required
def send_message(conv_id):
    conv = db.session.get(Conversation, conv_id)
    if not conv:
        return redirect(url_for('messaging.index'))
    if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
        flash("Acces non autorise.", 'danger')
        return redirect(url_for('messaging.index'))

    content = request.form.get('content', '').strip()
    other_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id

    if content:
        db.session.add(Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            content=content
        ))
        db.session.add(Notification(
            user_id=other_id, type='message',
            content=f"Nouveau message de {current_user.full_name}"
        ))
        db.session.commit()

    return redirect(url_for('messaging.open_conversation', other_id=other_id))


@messaging_bp.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False)\
                               .order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([{
        'id': n.id, 'type': n.type, 'content': n.content,
        'time': n.created_at.strftime('%H:%M')
    } for n in notifs])


@messaging_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    for n in Notification.query.filter_by(user_id=current_user.id, is_read=False).all():
        n.is_read = True
    db.session.commit()
    return jsonify({'ok': True})


# ── SocketIO ──
@socketio.on('join')
def on_join(data):
    join_room(str(data.get('conv_id')))

@socketio.on('leave')
def on_leave(data):
    leave_room(str(data.get('conv_id')))

@socketio.on('send_message')
def on_send_message(data):
    from flask_login import current_user as cu
    conv_id = data.get('conv_id')
    content = data.get('content', '').strip()
    if not content or not conv_id:
        return

    conv = db.session.get(Conversation, conv_id)
    if not conv:
        return
    if conv.user1_id != cu.id and conv.user2_id != cu.id:
        return

    msg = Message(conversation_id=conv.id, sender_id=cu.id, content=content)
    db.session.add(msg)
    other_id = conv.user2_id if conv.user1_id == cu.id else conv.user1_id
    db.session.add(Notification(
        user_id=other_id, type='message',
        content=f"Nouveau message de {cu.full_name}"
    ))
    db.session.commit()

    # Emettre SEULEMENT aux autres (include_self=False)
    emit('new_message', {
        'sender_id':   cu.id,
        'sender_name': cu.full_name,
        'content':     content,
        'time':        msg.sent_at.strftime('%H:%M'),
        'msg_id':      msg.id,
    }, room=str(conv_id), include_self=False)
