from moments.core.extensions import db
from moments.models import Photo, User
from tests import BaseTestCase


class AjaxTestCase(BaseTestCase):
    def test_notifications_count(self):
        response = self.client.get('/ajax/notifications-count')
        data = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Login required.')

        self.login()
        response = self.client.get('/ajax/notifications-count')
        self.assertEqual(response.status_code, 200)

    def test_get_profile(self):
        response = self.client.get('/ajax/profile/1')
        data = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Admin', data)

    def test_followers_count(self):
        response = self.client.get('/ajax/followers-count/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 0)

        user = db.session.get(User, 2)
        user.follow(db.session.get(User, 1))

        response = self.client.get('/ajax/followers-count/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 1)

    def test_collectors_count(self):
        response = self.client.get('/ajax/collectors-count/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 0)

        user = db.session.get(User, 1)
        user.collect(db.session.get(Photo, 1))

        response = self.client.get('/ajax/collectors-count/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['count'], 1)

    def test_collect(self):
        response = self.client.post('/ajax/collect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Login required.')

        self.login(email='unconfirmed@helloflask.com', password='123')
        response = self.client.post('/ajax/collect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Confirm account required.')
        self.logout()

        self.login()
        response = self.client.post('/ajax/collect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Photo collected.')

        response = self.client.post('/ajax/collect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Already collected.')

    def test_uncollect(self):
        response = self.client.post('/ajax/uncollect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Login required.')

        self.login()
        response = self.client.post('/ajax/uncollect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Not collect yet.')

        user = db.session.get(User, 2)
        user.collect(db.session.get(Photo, 1))

        response = self.client.post('/ajax/uncollect/1')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Collect canceled.')

    def test_follow(self):
        response = self.client.post('/ajax/follow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Login required.')

        self.login(email='unconfirmed@helloflask.com', password='123')
        response = self.client.post('/ajax/follow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Confirm account required.')
        self.logout()

        self.login()
        response = self.client.post('/ajax/follow/normal')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Already followed.')

        response = self.client.post('/ajax/follow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'User followed.')

    def test_unfollow(self):
        response = self.client.post('/ajax/unfollow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Login required.')

        self.login()
        response = self.client.post('/ajax/unfollow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Not following yet.')

        user = db.session.get(User, 2)
        user.follow(db.session.get(User, 1))

        response = self.client.post('/ajax/unfollow/admin')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Follow canceled.')
