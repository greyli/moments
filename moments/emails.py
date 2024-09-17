from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from moments.core.extensions import mail


def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


def send_mail(to, subject, template, **kwargs):
    if current_app.debug:
        current_app.logger.debug('Skip sending email in debug mode.')
        current_app.logger.debug(f'To: {to}')
        current_app.logger.debug(f'Subject: {subject}')
        current_app.logger.debug(f'Template: {template}')
        return
    message = Message(current_app.config['MOMENTS_MAIL_SUBJECT_PREFIX'] + subject, recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    app = current_app._get_current_object()
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr


def send_confirmation_email(user, token, to=None):
    send_mail(subject='Email Confirmation', to=to or user.email, template='emails/confirmation', user=user, token=token)


def send_reset_password_email(user, token):
    send_mail(subject='Password Reset', to=user.email, template='emails/reset_password', user=user, token=token)


def send_change_email_email(user, token, to=None):
    send_mail(
        subject='Change Email Confirmation', to=to or user.email, template='emails/change_email', user=user, token=token
    )
