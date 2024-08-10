from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import func, select

from moments.core.extensions import db
from moments.models import Notification, Photo, User
from moments.notifications import push_collect_notification, push_follow_notification

ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/notifications-count')
def notifications_count():
    if not current_user.is_authenticated:
        return {'message': 'Login required.'}, 403

    count = db.session.scalar(select(func.count(Notification.id)).filter_by(receiver_id=current_user.id, is_read=False))
    return {'count': count}


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = db.get_or_404(User, user_id)
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = db.get_or_404(User, user_id)
    return {'count': user.followers_count}


@ajax_bp.route('/collectors-count/<int:photo_id>')
def collectors_count(photo_id):
    photo = db.get_or_404(Photo, photo_id)
    return {'count': photo.collectors_count}


@ajax_bp.route('/collect/<int:photo_id>', methods=['POST'])
def collect(photo_id):
    if not current_user.is_authenticated:
        return {'message': 'Login required.'}, 403
    if not current_user.confirmed:
        return {'message': 'Confirm account required.'}, 400
    if not current_user.can('COLLECT'):
        return {'message': 'No permission.'}, 403

    photo = db.get_or_404(Photo, photo_id)
    if current_user.is_collecting(photo):
        return {'message': 'Already collected.'}, 400

    current_user.collect(photo)
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(user=current_user, photo_id=photo_id, receiver=photo.author)
    return {'message': 'Photo collected.'}


@ajax_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
def uncollect(photo_id):
    if not current_user.is_authenticated:
        return {'message': 'Login required.'}, 403

    photo = db.get_or_404(Photo, photo_id)
    if not current_user.is_collecting(photo):
        return {'message': 'Not collect yet.'}, 400

    current_user.uncollect(photo)
    return {'message': 'Collect canceled.'}


@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return {'message': 'Login required.'}, 403
    if not current_user.confirmed:
        return {'message': 'Confirm account required.'}, 400
    if not current_user.can('FOLLOW'):
        return {'message': 'No permission.'}, 403

    user = db.first_or_404(select(User).filter_by(username=username))
    if current_user.is_following(user):
        return {'message': 'Already followed.'}, 400

    current_user.follow(user)
    if user.receive_collect_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return {'message': 'User followed.'}


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return {'message': 'Login required.'}, 403

    user = db.first_or_404(select(User).filter_by(username=username))
    if not current_user.is_following(user):
        return {'message': 'Not follow yet.'}, 400

    current_user.unfollow(user)
    return {'message': 'Follow canceled.'}
