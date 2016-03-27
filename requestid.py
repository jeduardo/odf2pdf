from flask import make_response, request
from functools import wraps, update_wrapper


def requestid(view):
    @wraps(view)
    def request_id(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        id = request.headers.get('X-Request-Id')
        if id:
            response.headers['X-Request-Id'] = id
        return response

    return update_wrapper(request_id, view)