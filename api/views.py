from flask import Flask, jsonify, request, make_response, Blueprint
from api.middlewares import requires_auth
from api.models import UserSchema, BoardSchema, CommentSchema
from api import db as database
from api.db import db as redis

mod = Blueprint('views', __name__)

user_schema = UserSchema()
board_schema = BoardSchema()
comment_schema = CommentSchema()


@mod.route('/', methods=['GET'])
@requires_auth
def index():
    boards = database.get_boards()
    return make_response(jsonify(boards), 200)


@mod.route('/<board_id>', methods=['GET'])
@requires_auth
def single_board(board_id):
    board = database.get_board(board_id)
    if board is None:
        return jsonify({'message': 'Board is not present'}, 404)
    else:
        return make_response(jsonify(board), 200)


@mod.route('/sign_up', methods=['POST'])
def insert_user():
    inputs = request.get_json(request)
    user = user_schema.load(inputs)
    if len(user.errors) == 0:
        msg, code = database.insert_user(user.data)
    else:
        msg, code = user.errors, 400
    return make_response(jsonify(msg), code)


@mod.route('/', methods=['POST'])
@requires_auth
def insert_board():
    inputs = request.get_json(request)
    board = board_schema.load(inputs)
    if len(board.errors) == 0:
        msg, code = database.insert_board(board.data)
    else:
        msg, code = board.errors, 400
    return make_response(jsonify(msg), code)


@mod.route('/<board_id>/like', methods=['PUT'])
@requires_auth
def like_board(board_id):
    board = database.get_board(board_id)
    if board is None:
        return make_response(jsonify({'message': 'Board is not present'}), 400)
    else:
        likes = redis.incrby('likes:board:' + board_id, 1)
        return make_response(jsonify({'status': 'Success', 'count': likes}), 200)


@mod.route('/<board_id>/insert_comment', methods=['POST'])
@requires_auth
def insert_comment(board_id):
    inputs = request.get_json(request)
    comment = comment_schema.load(inputs)
    if len(comment.errors) == 0:
        msg, code = database.insert_comment(board_id, comment.data)
    else:
        msg, code = comment.errors, 400
    return make_response(jsonify(msg), code)


def get_user_from_header():
    user = request.headers.get('Authorization')
    if user is not None and user.find(':') != -1:
        separator_position = user.find(':')
        user = user[:separator_position]
    return user
