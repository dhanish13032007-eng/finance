"""
Notifications Routes
Manage User Alerts (unread count, fetch all, mark as read).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification
from utils.helpers import success_response, error_response

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Fetch all notifications for the user."""
    user_id = int(get_jwt_identity())
    
    # We could paginate, but let's just return top 50
    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    return success_response({
        'notifications': [n.to_dict() for n in notifs],
        'unread_count': unread_count
    })


@notifications_bp.route('/api/notifications/<int:notif_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notif_id):
    """Mark a notification as read."""
    user_id = int(get_jwt_identity())
    notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if not notif:
        return error_response('Notification not found', 404)
        
    notif.is_read = True
    db.session.commit()
    
    return success_response(notif.to_dict(), 'Notification marked as read')


@notifications_bp.route('/api/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all unread notifications as read."""
    user_id = int(get_jwt_identity())
    notifs = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    for n in notifs:
        n.is_read = True
        
    db.session.commit()
    return success_response(message='All notifications marked as read')
