from flask_sqlalchemy import get_debug_queries


def register_request_handlers(app):
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            if q.duration >= app.config['MOMENTS_SLOW_QUERY_THRESHOLD']:
                app.logger.warning(
                    'Slow query: Duration: '
                    f'{q.duration:f}s\n Context: {q.context}\nQuery: {q.statement}\n'
                )
        return response
