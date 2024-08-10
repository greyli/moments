from moments.core.extensions import db
from moments.models import Role, Tag, User
from tests import BaseTestCase


class AdminTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login(email='admin@helloflask.com', password='123')

    def test_index_page(self):
        response = self.client.get('/admin/', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Moments Dashboard', data)

    def test_bad_permission(self):
        self.logout()
        response = self.client.get('/admin/', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Please log in to access this page.', data)
        self.assertNotIn('Moments Dashboard', data)

        self.login()  # normal user, without MODERATOR permission
        response = self.client.get('/admin/')
        data = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('Moments Dashboard', data)

    def test_edit_profile_admin(self):
        role_id = Role.query.filter_by(name='Locked').first().id
        response = self.client.post(
            '/admin/profile/2',
            data=dict(
                username='newname',
                role=role_id,
                confirmed=True,
                active=True,
                name='New Name',
                email='new@helloflask.com',
            ),
            follow_redirects=True,
        )
        data = response.get_data(as_text=True)
        self.assertIn('Profile updated.', data)
        user = db.session.get(User, 2)
        self.assertEqual(user.name, 'New Name')
        self.assertEqual(user.username, 'newname')
        self.assertEqual(user.email, 'new@helloflask.com')
        self.assertEqual(user.role.name, 'Locked')

    def test_block_user(self):
        response = self.client.post('/admin/block/user/2', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Account blocked.', data)
        user = db.session.get(User, 2)
        self.assertEqual(user.active, False)

    def test_unblock_user(self):
        user = db.session.get(User, 2)
        user.active = False
        db.session.commit()
        self.assertEqual(user.active, False)

        response = self.client.post('/admin/unblock/user/2', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Block canceled.', data)
        user = db.session.get(User, 2)
        self.assertEqual(user.active, True)

    def test_lock_user(self):
        response = self.client.post('/admin/lock/user/2', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Account locked.', data)
        user = db.session.get(User, 2)
        self.assertEqual(user.role.name, 'Locked')

    def test_unlock_user(self):
        user = db.session.get(User, 2)
        user.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()
        self.assertEqual(user.role.name, 'Locked')

        response = self.client.post('/admin/unlock/user/2', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Lock canceled.', data)
        user = db.session.get(User, 2)
        self.assertEqual(user.role.name, 'User')

    def test_delete_tag(self):
        tag = Tag(name='test')
        db.session.add(tag)
        db.session.commit()
        self.assertIsNotNone(db.session.get(Tag, 1))

        response = self.client.post('/admin/delete/tag/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Tag deleted.', data)
        self.assertEqual(db.session.get(Tag, 1), None)

    def test_manage_user_page(self):
        response = self.client.get('/admin/manage/user')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Users', data)
        self.assertIn('Admin', data)
        self.assertIn('Locked', data)
        self.assertIn('Normal', data)

        response = self.client.get('/admin/manage/user?filter=locked')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Users', data)
        self.assertIn('Locked User', data)
        self.assertNotIn('Normal User', data)

        response = self.client.get('/admin/manage/user?filter=blocked')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Users', data)
        self.assertIn('Blocked User', data)
        self.assertNotIn('Locked User', data)
        self.assertNotIn('Normal User', data)

        response = self.client.get('/admin/manage/user?filter=administrator')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Users', data)
        self.assertIn('Admin', data)
        self.assertNotIn('Blocked User', data)
        self.assertNotIn('Locked User', data)
        self.assertNotIn('Normal User', data)

        response = self.client.get('/admin/manage/user?filter=moderator')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Users', data)
        self.assertIn('Admin', data)
        self.assertNotIn('Blocked User', data)
        self.assertNotIn('Locked User', data)
        self.assertNotIn('Normal User', data)

    def test_manage_photo_page(self):
        response = self.client.get('/admin/manage/photo')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Photos', data)
        self.assertIn('Order by flag', data)

        response = self.client.get('/admin/manage/photo/by_time')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Photos', data)
        self.assertIn('Order by time', data)

    def test_manage_tag_page(self):
        response = self.client.get('/admin/manage/tag')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Tags', data)

    def test_manage_comment_page(self):
        response = self.client.get('/admin/manage/comment')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Comments', data)
        self.assertIn('Order by flag', data)

        response = self.client.get('/admin/manage/comment/by_time')
        data = response.get_data(as_text=True)
        self.assertIn('Manage Comments', data)
        self.assertIn('Order by time', data)
