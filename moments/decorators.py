from functools import wraps

from flask import flash, url_for, redirect, abort
from markupsafe import Markup
from flask_login import current_user


def confirm_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            resend_url = url_for('auth.resend_confirmation_email')
            message = Markup(
                'Please confirm your account first.'
                'Not receive the email?'
                f'<a class="alert-link" href="{resend_url}">Resend Confirm Email</a>')
            flash(message, 'warning')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_function


def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(func):
    return permission_required('ADMINISTER')(func)
