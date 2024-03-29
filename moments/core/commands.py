import click

from moments.core.extensions import db
from moments.models import Role


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    def init():
        """Initialize Moments."""
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows, default is 30.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 30.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 20.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 50.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 100.')
    def fake(user, follow, photo, tag, collect, comment):
        """Generate fake data."""

        from moments.fakes import fake_admin, fake_comment, fake_follow, fake_photo, fake_tag, fake_user, fake_collect

        db.drop_all()
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()
        click.echo('Generating the administrator...')
        fake_admin()
        click.echo(f'Generating {user} users...')
        fake_user(user)
        click.echo(f'Generating {follow} follows...')
        fake_follow(follow)
        click.echo(f'Generating {tag} tags...')
        fake_tag(tag)
        click.echo(f'Generating {photo} photos...')
        fake_photo(photo)
        click.echo(f'Generating {collect} collects...')
        fake_collect(collect)
        click.echo(f'Generating {comment} comments...')
        fake_comment(comment)
        click.echo('Done.')
