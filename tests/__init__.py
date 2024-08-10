import unittest

from moments import create_app
from moments.core.extensions import db
from moments.models import Comment, Photo, Role, Tag, User


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()
        self.cli_runner = self.app.test_cli_runner()

        db.create_all()
        Role.init_role()

        admin_user = User(email='admin@helloflask.com', name='Admin', username='admin', password='123', confirmed=True)
        normal_user = User(
            email='normal@helloflask.com', name='Normal User', username='normal', password='123', confirmed=True
        )
        unconfirmed_user = User(
            email='unconfirmed@helloflask.com',
            name='Unconfirmed',
            username='unconfirmed',
            password='123',
            confirmed=False,
        )
        locked_user = User(
            email='locked@helloflask.com',
            name='Locked User',
            username='locked',
            password='123',
            confirmed=True,
            locked=True,
        )
        locked_user.lock()
        blocked_user = User(
            email='blocked@helloflask.com',
            name='Blocked User',
            username='blocked',
            password='123',
            confirmed=True,
            active=False,
        )
        photo = Photo(
            filename='test.jpg',
            filename_s='test_s.jpg',
            filename_m='test_m.jpg',
            description='Photo 1',
            author=admin_user,
        )
        photo2 = Photo(
            filename='test2.jpg',
            filename_s='test_s2.jpg',
            filename_m='test_m2.jpg',
            description='Photo 2',
            author=normal_user,
        )

        comment = Comment(body='test comment body', photo=photo, author=normal_user)
        tag = Tag(name='test tag')
        photo.tags.append(tag)
        db.session.add_all([admin_user, normal_user, unconfirmed_user, locked_user, blocked_user, comment, photo2])
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.context.pop()

    def login(self, email=None, password=None):
        if email is None and password is None:
            email = 'normal@helloflask.com'
            password = '123'

        return self.client.post('/auth/login', data=dict(email=email, password=password), follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)
