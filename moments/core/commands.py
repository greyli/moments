import click

from moments.core.extensions import db
from moments.models import Role


def register_commands(app):
    @app.cli.command('init-db')
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def init_db_command(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command('init-app')
    def init_app_command():
        """Initialize Moments."""
        db.create_all()
        click.echo('Initialized the database.')

        Role.init_role()
        click.echo('Initialized the roles and permissions.')

    @app.cli.command('lorem')
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows, default is 30.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 30.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 20.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 50.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 100.')
    def lorem_command(user, follow, photo, tag, collect, comment):
        """Generate fake data."""
        from moments.lorem import fake_admin, fake_collect, fake_comment, fake_follow, fake_photo, fake_tag, fake_user

        db.drop_all()
        db.create_all()

        Role.init_role()
        click.echo('Initialized the roles and permissions.')
        fake_admin()
        click.echo('Generated the administrator.')
        fake_user(user)
        click.echo(f'Generated {user} users.')
        fake_follow(follow)
        click.echo(f'Generated {follow} follows.')
        fake_tag(tag)
        click.echo(f'Generated {tag} tags.')
        fake_photo(photo)
        click.echo(f'Generated {photo} photos.')
        fake_collect(collect)
        click.echo(f'Generated {collect} collects.')
        fake_comment(comment)
        click.echo(f'Generated {comment} comments.')
        click.echo('Done.')
