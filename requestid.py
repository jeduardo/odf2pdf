from flask import make_response, request, g, has_app_context, has_request_context
from functools import wraps, update_wrapper
from logging import Filter
from uuid import uuid4


# Filter to add request ID to logger
class RequestIdFilter(Filter):
    def filter(self, record):
        if has_app_context():
            if getattr(g, 'request_id', None):
                record.request_id = g.request_id
            else:
                headers = request.headers
                fetch_id = headers['X-Request-Id'] if has_request_context() and 'X-Request-Id' in headers.keys() else uuid4()
                record.request_id = fetch_id
                g.request_id = fetch_id
        else:
            record.request_id = 'INTERNAL'
        return True


# Decorator to add request id to request output
def requestid(view):
    @wraps(view)
    def request_id(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        id = request.headers.get('X-Request-Id') or getattr(g, 'request_id', None)
        if id:
            response.headers['X-Request-Id'] = id
        return response

    return update_wrapper(request_id, view)