from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email
from sqlalchemy import select

from moments.forms.user import EditProfileForm
from moments.core.extensions import db
from moments.models import User, Role


class EditProfileAdminForm(EditProfileForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    role = SelectField('Role', coerce=int)
    active = BooleanField('Active')
    confirmed = BooleanField('Confirmed')
    submit = SubmitField()

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        roles = db.session.execute(
            select(Role).order_by(Role.name)
        ).scalars().all()
        self.role.choices = [(role.id, role.name) for role in roles]
        self.user = user

    def validate_username(self, field):
        user = db.session.execute(
            select(User).filter_by(username=field.data)
        ).scalar()
        if field.data != self.user.username and user:
            raise ValidationError('The username is already in use.')

    def validate_email(self, field):
        email = db.session.execute(
            select(User).filter_by(email=field.data.lower())
        ).scalar()
        if field.data != self.user.email and email:
            raise ValidationError('The email is already in use.')
