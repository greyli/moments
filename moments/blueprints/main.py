from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select
from sqlalchemy.orm import with_parent

from moments.core.extensions import db
from moments.decorators import confirm_required, permission_required
from moments.forms.main import CommentForm, DescriptionForm, TagForm
from moments.models import Collection, Comment, Follow, Notification, Photo, Tag, User
from moments.notifications import push_collect_notification, push_comment_notification
from moments.utils import flash_errors, redirect_back, rename_image, resize_image, validate_image

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['MOMENTS_PHOTO_PER_PAGE']
        stmt = (
            select(Photo)
            .join(Follow, Follow.followed_id == Photo.author_id)
            .filter(Follow.follower_id == current_user.id)
            .order_by(Photo.created_at.desc())
        )
        pagination = db.paginate(stmt, page=page, per_page=per_page)
        photos = pagination.items
    else:
        pagination = None
        photos = None
    stmt = (
        select(Tag)
        .join(Tag.photos)
        .group_by(Tag.id)
        .order_by(func.count(Photo.id).desc())
        .limit(10)
    )
    tags = db.session.scalars(stmt).all()
    return render_template('main/index.html', pagination=pagination, photos=photos, tags=tags)


@main_bp.route('/explore')
def explore():
    stmt = select(Photo).order_by(func.random()).limit(12)
    photos = db.session.scalars(stmt).all()
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/search')
def search():
    q = request.args.get('q').strip()
    if not q:
        flash('Enter keyword about photo, user or tag.', 'warning')
        return redirect_back()

    category = request.args.get('category', 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_SEARCH_RESULT_PER_PAGE']
    # TODO: add SQLAlchemy 2.x support to Flask-Whooshee then update the following code
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page=page, per_page=per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page=page, per_page=per_page)
    else:
        pagination = Photo.query.whooshee_search(q).paginate(page=page, per_page=per_page)
    results = pagination.items
    return render_template('main/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_NOTIFICATION_PER_PAGE']
    stmt = current_user.notifications.select()
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        stmt = stmt.filter_by(is_read=False)

    pagination = db.paginate(stmt.order_by(Notification.created_at.desc()), page=page, per_page=per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = db.session.get(Notification, notification_id) or abort(404)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    stmt = current_user.notifications.select().filter_by(is_read=False)
    notifications = db.session.scalars(stmt).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['MOMENTS_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No image.', 400
        f = request.files.get('file')
        if not validate_image(f.filename):
            return 'Invalid image.', 400
        filename = rename_image(f.filename)
        f.save(current_app.config['MOMENTS_UPLOAD_PATH'] / filename)
        filename_s = resize_image(f, filename, current_app.config['MOMENTS_PHOTO_SIZES']['small'])
        filename_m = resize_image(f, filename, current_app.config['MOMENTS_PHOTO_SIZES']['medium'])
        photo = Photo(
            filename=filename, filename_s=filename_s, filename_m=filename_m, author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')


@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_COMMENT_PER_PAGE']
    pagination = db.paginate(
        select(Comment).filter_by(photo_id=photo.id).order_by(Comment.created_at.asc()), page=page, per_page=per_page
    )
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = photo.description
    return render_template(
        'main/photo.html',
        photo=photo,
        comment_form=comment_form,
        description_form=description_form,
        tag_form=tag_form,
        pagination=pagination,
        comments=comments,
    )


@main_bp.route('/photo/n/<int:photo_id>')
def get_next_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    stmt = (
        select(Photo)
        .filter(with_parent(photo.author, User.photos), Photo.created_at < photo.created_at)
        .order_by(Photo.created_at.desc())
    )
    next_photo = db.session.scalar(stmt)

    if next_photo is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=next_photo.id))


@main_bp.route('/photo/p/<int:photo_id>')
def get_previous_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    stmt = (
        select(Photo)
        .filter(with_parent(photo.author, User.photos), Photo.created_at > photo.created_at)
        .order_by(Photo.created_at.asc())
    )
    previous_photo = db.session.scalar(stmt)
    if previous_photo is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=previous_photo.id))


@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if current_user.is_collecting(photo):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash('Photo collected.', 'success')
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(user=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if not current_user.is_collecting(photo):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = db.session.get(Comment, comment_id) or abort(404)
    comment.flag += 1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/photo/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    photo.flag += 1
    db.session.commit()
    flash('Photo reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=photo.id))


@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOMENTS_USER_PER_PAGE']
    stmt = photo.collections.select().order_by(Collection.created_at.desc())
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    collections = pagination.items
    return render_template('main/collectors.html', collections=collections, photo=photo, pagination=pagination)


@main_bp.route('/photo/<int:photo_id>/description', methods=['POST'])
@login_required
def edit_description(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = db.session.get(Comment, replied_id) or abort(404)
            push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != photo.author:
            push_comment_notification(photo_id, receiver=photo.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = db.session.scalar(select(Tag).filter_by(name=name))
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/set-comment/<int:photo_id>', methods=['POST'])
@login_required
def set_comment(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if current_user != photo.author:
        abort(403)

    if photo.can_comment:
        photo.can_comment = False
        flash('Comment disabled', 'info')
    else:
        photo.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = db.session.get(Comment, comment_id) or abort(404)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id, author=comment.author.name)
        + '#comment-form'
    )


@main_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'info')

    base_stmt = select(Photo).filter(with_parent(photo.author, User.photos))
    next_photo = db.session.scalar(
        base_stmt.filter(Photo.created_at < photo.created_at).order_by(Photo.created_at.desc())
    )
    if next_photo is None:
        previous_photo = db.session.scalar(
            base_stmt.filter(Photo.created_at > photo.created_at).order_by(Photo.created_at.asc())
        )
        if previous_photo is None:
            return redirect(url_for('user.index', username=photo.author.username))
        return redirect(url_for('.show_photo', photo_id=previous_photo.id))
    return redirect(url_for('.show_photo', photo_id=next_photo.id))


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id) or abort(404)
    if current_user != comment.author and current_user != comment.photo.author and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/tag/<int:tag_id>')
def show_tag(tag_id):
    tag = db.session.get(Tag, tag_id) or abort(404)
    page = request.args.get('page', 1, type=int)
    order_rule = request.args.get('order_rule', 'time')
    per_page = current_app.config['MOMENTS_PHOTO_PER_PAGE']
    stmt = tag.photos.select().order_by(Photo.created_at.desc())
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    photos = pagination.items

    if order_rule == 'collections':
        photos.sort(key=lambda x: x.collectors_count, reverse=True)
    return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(photo_id, tag_id):
    photo = db.session.get(Photo, photo_id) or abort(404)
    tag = db.session.get(Tag, tag_id) or abort(404)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    tag_photos = db.session.scalars(tag.photos.select()).all()
    if not tag_photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))
