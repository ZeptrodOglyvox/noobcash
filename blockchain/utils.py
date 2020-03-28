import functools

from Crypto.Hash import SHA1
from Crypto.Signature import PKCS1_v1_5
from flask import request, make_response, jsonify


def verify_signature(transaction, signature):
    h = SHA1.new(str(transaction.to_dict()).encode('utf8'))
    try:
        cipher = PKCS1_v1_5.new(transaction.sender_address)
        cipher.verify(h, signature)
        return True
    except (ValueError, TypeError):
        return 'Invalid Signature.'


def required_fields(fields):
    def wrapper(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            data = request.get_json()

            if not all(k in data for k in fields):
                response = dict(message='Required Fields Missing')
                status_code = 400
                return make_response(jsonify(response)), status_code
            else:
                return view(*args, **kwargs)

        return wrapped_view
    return wrapper