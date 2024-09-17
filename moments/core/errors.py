from flask import render_template
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return render_template('errors/400.html', description=error.description), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', description=error.description), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', description=error.description), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('errors/413.html', description=error.description), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', description=error.description), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        description = 'Session expired, return last page and try again.'
        return render_template('errors/400.html', description=description), 500
