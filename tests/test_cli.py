from moments.core.extensions import db
from moments.models import Comment, Photo, Role, Tag, User
from tests import BaseTestCase


class CLITestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        db.drop_all()

    def test_init_db_command(self):
        result = self.cli_runner.invoke(args=['init-db'])
        self.assertIn('Initialized database.', result.output)

    def test_init_db_command_with_drop(self):
        result = self.cli_runner.invoke(args=['init-db', '--drop'], input='y\n')
        self.assertIn('This operation will delete the database, do you want to continue?', result.output)
        self.assertIn('Drop tables.', result.output)

    def test_init_app_command(self):
        result = self.cli_runner.invoke(args=['init-app'])
        self.assertIn('Initialized the database.', result.output)
        self.assertIn('Initialized the roles and permissions.', result.output)
        self.assertEqual(Role.query.count(), 4)

    def test_lorem_command(self):
        pass  # it will take too long time

    def test_lorem_command_with_count(self):
        result = self.cli_runner.invoke(
            args=[
                'lorem',
                '--user',
                '5',
                '--follow',
                '10',
                '--photo',
                '10',
                '--tag',
                '10',
                '--collect',
                '10',
                '--comment',
                '10',
            ]
        )

        self.assertIn('Initialized the roles and permissions.', result.output)

        self.assertEqual(User.query.count(), 6)
        self.assertIn('Generated the administrator.', result.output)

        self.assertIn('Generated 10 follows.', result.output)

        self.assertEqual(Photo.query.count(), 10)
        self.assertIn('Generated 10 photos.', result.output)

        self.assertEqual(Tag.query.count(), 10)
        self.assertIn('Generated 10 tags.', result.output)

        self.assertIn('Generated 10 collects.', result.output)

        self.assertEqual(Comment.query.count(), 10)
        self.assertIn('Generated 10 comments.', result.output)
