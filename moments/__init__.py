from flask import Flask

from moments.blueprints.admin import admin_bp
from moments.blueprints.ajax import ajax_bp
from moments.blueprints.auth import auth_bp
from moments.blueprints.main import main_bp
from moments.blueprints.user import user_bp
from moments.core.commands import register_commands
from moments.core.errors import register_error_handlers
from moments.core.extensions import avatars, bootstrap, csrf, db, dropzone, login_manager, mail, whooshee
from moments.core.logging import register_logging
from moments.core.request import register_request_handlers
from moments.core.templating import register_template_handlers
from moments.settings import config


def create_app(config_name):
    app = Flask('moments')

    app.config.from_object(config[config_name])

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    dropzone.init_app(app)
    whooshee.init_app(app)
    avatars.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')

    register_commands(app)
    register_logging(app)
    register_template_handlers(app)
    register_request_handlers(app)
    register_error_handlers(app)

    return app
