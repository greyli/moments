import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
from pathlib import Path

import jwt
import PIL
from flask import current_app, flash, redirect, request, url_for
from jwt.exceptions import InvalidTokenError
from PIL import Image


def generate_token(user, operation, expiration=3600, **kwargs):
    payload = {
        'id': user.id,
        'operation': operation.value,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)
    }
    payload.update(**kwargs)
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def parse_token(user, token, operation):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except InvalidTokenError:
        return {}

    if operation.value != payload.get('operation') or user.id != payload.get('id'):
        return {}
    return payload


def rename_image(old_filename):
    ext = Path(old_filename).suffix
    new_filename = uuid.uuid4().hex + ext
    return new_filename


def resize_image(image, filename, base_width):
    ext = Path(filename).suffix
    img = Image.open(image)
    if img.size[0] <= base_width:
        return filename
    w_percent = base_width / float(img.size[0])
    h_size = int(float(img.size[1]) * float(w_percent))
    img = img.resize((base_width, h_size), PIL.Image.LANCZOS)

    filename += current_app.config['MOMENTS_PHOTO_SUFFIXES'][base_width] + ext
    img.save(current_app.config['MOMENTS_UPLOAD_PATH'] / filename, optimize=True, quality=85)
    return filename


def validate_image(filename):
    ext = Path(filename).suffix.lower()
    allowed_extensions = current_app.config['DROPZONE_ALLOWED_FILE_TYPE'].split(',')
    return '.' in filename and ext in allowed_extensions


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default='main.index', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in the {getattr(form, field).label.text} field - {error}')
