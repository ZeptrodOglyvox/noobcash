import functools

from flask import request, make_response, jsonify


def required_fields(fields):
    def wrapper(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            data = request.get_json()

            if data is None or not all(k in data for k in fields):
                response = dict(message='Required fields missing.')
                status_code = 400
                return make_response(jsonify(response)), status_code
            else:
                return view(*args, **kwargs)

        return wrapped_view
    return wrapper
