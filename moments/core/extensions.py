from flask_avatars import Avatars
from flask_bootstrap import Bootstrap5
from flask_dropzone import Dropzone
from flask_login import AnonymousUserMixin, LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        }
    )


bootstrap = Bootstrap5()
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
dropzone = Dropzone()
whooshee = Whooshee()
avatars = Avatars()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    from moments.models import User

    user = db.session.get(User, int(user_id))
    return user


login_manager.login_view = 'auth.login'
# login_manager.login_message = 'Your custom message'
login_manager.login_message_category = 'warning'

login_manager.refresh_view = 'auth.re_authenticate'
# login_manager.needs_refresh_message = 'Your custom message'
login_manager.needs_refresh_message_category = 'warning'


class Guest(AnonymousUserMixin):
    def can(self, permission_name):
        return False

    @property
    def is_admin(self):
        return False


login_manager.anonymous_user = Guest
