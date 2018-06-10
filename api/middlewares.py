import hashlib
from functools import wraps
from flask import request, jsonify, make_response
from api.db import db


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = check_auth()
        if not auth:
            return make_response(jsonify({'message': 'Authorization is required'}), 401)
        return f(*args, **kwargs)

    return decorated


def check_auth():
    header = request.headers.get('Authorization')
    if header is not None and header.find(':') != -1:
        separator_position = header.find(':')
        username = header[:separator_position]
        password_hash = hashlib.md5(header[separator_position + 1:].encode('utf-8')).hexdigest()
        present_maybe = db.get('user:' + username).decode('utf-8')
        if len(present_maybe) > 0 and password_hash == present_maybe:
            return True
    return False
