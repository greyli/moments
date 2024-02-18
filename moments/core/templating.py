from flask_login import current_user
from sqlalchemy import select, func

from moments.core.extensions import db
from moments.models import Notification


def register_template_handlers(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = db.session.execute(
                select(func.count(Notification.id)).filter_by(receiver_id=current_user.id, is_read=False)
            ).scalars().one()
        else:
            notification_count = None
        return dict(notification_count=notification_count)

