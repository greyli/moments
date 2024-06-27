from moments import create_app
from moments.core.extensions import db
from moments.models import Comment, Photo, Role, User

app = create_app('testing')
with app.app_context():
    db.create_all()

    Role.init_role()

    admin_user = User(email='admin@helloflask.com', name='Admin', username='admin', password='123', confirmed=True)
    normal_user = User(
        email='normal@helloflask.com', name='Normal User', username='normal', password='123', confirmed=True
    )
    photo = Photo(
        filename='test.jpg', filename_s='test_s.jpg', filename_m='test_m.jpg', description='Photo 1', author=admin_user
    )
    comment = Comment(body='test comment body', photo=photo, author=normal_user)
    db.session.add_all([admin_user, normal_user, comment])
    db.session.commit()
