import hashlib
from functools import wraps
from flask import request, jsonify, make_response
from api.db import db


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = check_auth()
        if not auth:
            return make_response(jsonify({'message': 'Authorization error'}), 401)
        return f(*args, **kwargs)

    return decorated


def check_auth():
    header = request.headers.get('Authorization')
    if header is not None and header.find(':') != -1:
        separator_position = header.find(':')
        username = header[:separator_position]
        password_hash = hashlib.md5(header[separator_position + 1:].encode('utf-8')).hexdigest()
        present_maybe = db.get('user:' + username)
        if present_maybe is not None and len(present_maybe) > 0 and password_hash == present_maybe.decode('utf-8'):
            return True
    return False


def get_user_from_header():
    user = request.headers.get('Authorization')
    if user is not None and user.find(':') != -1:
        separator_position = user.find(':')
        user = user[:separator_position]
    return user


def action_callback(action):
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = get_user_from_header()
            counter = db.incrby('hourly' + action + ':user:' + username, 1)
            if counter is not None and counter == 1:
                db.expire('hourly' + action + ':user:' + username, 360)
            return func(*args, **kwargs)

        return wrapper

    return real_decorator


def check_permission_callback(action):
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = get_user_from_header()
            current_counter = db.get('hourly' + action + ':user:' + username)
            if current_counter is not None and int(current_counter.decode('utf-8')) > 5:
                return make_response(
                    jsonify({'message': 'You\'ve reached the limit'}), 401)
            return func(*args, **kwargs)

        return wrapper

    return real_decorator
