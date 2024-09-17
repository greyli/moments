from flask import Blueprint, current_app, flash, render_template, request, abort, redirect, url_for
from flask_login import login_required
from sqlalchemy import func, select

from moments.core.extensions import db
from moments.decorators import admin_required, permission_required
from moments.forms.admin import EditProfileAdminForm
from moments.models import Comment, Photo, Role, Tag, User
from moments.utils import redirect_back

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@permission_required('MODERATE')
def index():
    user_count = db.session.scalar(select(func.count(User.id)))
    locked_user_count = db.session.scalar(select(func.count(User.id)).filter_by(locked=True))
    blocked_user_count = db.session.scalar(select(func.count(User.id)).filter_by(active=False))
    photo_count = db.session.scalar(select(func.count(Photo.id)))
    reported_photos_count = db.session.scalar(select(func.count(Photo.id)).filter(Photo.flag > 0))
    tag_count = db.session.scalar(select(func.count(Tag.id)))
    comment_count = db.session.scalar(select(func.count(Comment.id)))
    reported_comments_count = db.session.scalar(select(func.count(Comment.id)).filter(Comment.flag > 0))
    return render_template(
        'admin/index.html',
        user_count=user_count,
        photo_count=photo_count,
        tag_count=tag_count,
        comment_count=comment_count,
        locked_user_count=locked_user_count,
        blocked_user_count=blocked_user_count,
        reported_comments_count=reported_comments_count,
        reported_photos_count=reported_photos_count,
    )


@admin_bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = db.session.get(User, user_id) or abort(404)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        role = db.session.get(Role, form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.bio = form.bio.data
        user.website = form.website.data
        user.confirmed = form.confirmed.data
        user.active = form.active.data
        user.location = form.location.data
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect_back()
    if request.method == 'GET':
        form.name.data = user.name
        form.role.data = user.role_id
        form.bio.data = user.bio
        form.website.data = user.website
        form.location.data = user.location
        form.username.data = user.username
        form.email.data = user.email
        form.confirmed.data = user.confirmed
        form.active.data = user.active
    return render_template('admin/edit_profile.html', form=form, user=user)


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def block_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role.name in ['Administrator', 'Moderator']:
        flash('Permission denied.', 'warning')
    else:
        user.block()
        flash('Account blocked.', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unblock_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    user.unblock()
    flash('Block canceled.', 'info')
    return redirect_back()


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def lock_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role.name in ['Administrator', 'Moderator']:
        flash('Permission denied.', 'warning')
    else:
        user.lock()
        flash('Account locked.', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unlock_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    user.unlock()
    flash('Lock canceled.', 'info')
    return redirect_back()


@admin_bp.route('/delete/tag/<int:tag_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def delete_tag(tag_id):
    tag = db.session.get(Tag, tag_id) or abort(404)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag deleted.', 'info')
    return redirect_back()


@admin_bp.route('/manage/user')
@login_required
@permission_required('MODERATE')
def manage_user():
    filter_rule = request.args.get('filter', 'all')  # 'all', 'locked', 'blocked', 'administrator', 'moderator'
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_MANAGE_USER_PER_PAGE']
    administrator = db.session.scalar(select(Role).filter_by(name='Administrator'))
    moderator = db.session.scalar(select(Role).filter_by(name='Moderator'))

    if filter_rule == 'locked':
        filtered_users = select(User).filter_by(locked=True)
    elif filter_rule == 'blocked':
        filtered_users = select(User).filter_by(active=False)
    elif filter_rule == 'administrator':
        filtered_users = select(User).filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filtered_users = select(User).filter_by(role=moderator)
    else:
        filtered_users = select(User)

    pagination = db.paginate(filtered_users.order_by(User.member_since.desc()), page=page, per_page=per_page)
    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)


@admin_bp.route('/manage/photo', defaults={'order': 'by_flag'})
@admin_bp.route('/manage/photo/<order>')
@login_required
@permission_required('MODERATE')
def manage_photo(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_MANAGE_PHOTO_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = db.paginate(select(Photo).order_by(Photo.created_at.desc()), page=page, per_page=per_page, error_out=False)
        order_rule = 'time'
    else:
        pagination = db.paginate(select(Photo).order_by(Photo.flag.desc()), page=page, per_page=per_page, error_out=False)
    if page > pagination.pages:
        return redirect(url_for('.manage_photo', page=pagination.pages, order_rule=order_rule))
    photos = pagination.items
    return render_template('admin/manage_photo.html', pagination=pagination, photos=photos, order_rule=order_rule)


@admin_bp.route('/manage/tag')
@login_required
@permission_required('MODERATE')
def manage_tag():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_MANAGE_TAG_PER_PAGE']
    pagination = db.paginate(select(Tag).order_by(Tag.id.desc()), page=page, per_page=per_page)
    tags = pagination.items
    return render_template('admin/manage_tag.html', pagination=pagination, tags=tags)


@admin_bp.route('/manage/comment', defaults={'order': 'by_flag'})
@admin_bp.route('/manage/comment/<order>')
@login_required
@permission_required('MODERATE')
def manage_comment(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_MANAGE_COMMENT_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = db.paginate(select(Comment).order_by(Comment.created_at.desc()), page=page, per_page=per_page, error_out=False)
        order_rule = 'time'
    else:
        pagination = db.paginate(select(Comment).order_by(Comment.flag.desc()), page=page, per_page=per_page, error_out=False)
    if page > pagination.pages:
        return redirect(url_for('.manage_comment', page=pagination.pages, order_rule=order_rule))
    comments = pagination.items
    return render_template('admin/manage_comment.html', pagination=pagination, comments=comments, order_rule=order_rule)


@admin_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def delete_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'info')
    return redirect_back()


@admin_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id) or abort(404)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect_back()
