from flask import Flask, jsonify, request, make_response
from app.models import UserSchema, BoardSchema, CommentSchema
from app.utils import EndpointAction, AdBoardInspector, AdBoardDB


class AdBoardViews(object):
    app = None
    user_schema = UserSchema()
    board_schema = BoardSchema()
    comment_schema = CommentSchema()

    def __init__(self, name):
        self.app = Flask(name)
        self.db = AdBoardDB({'host': 'localhost', 'port': 6379})

    def run(self):
        self.app.run()

    def add_url_rule(self, rule, endpoint=None, view_func=None, provide_automatic_options=None, **options):
        if view_func is not None:
            view_func = EndpointAction(view_func)
        self.app.add_url_rule(rule, endpoint, view_func, provide_automatic_options, **options)

    @AdBoardInspector.requires_auth
    def index(self):
        boards = self.db.get_boards()
        return make_response(jsonify(boards), 200)

    def single_board(self, board_id):
        board = self.db.get_board(board_id)
        if board is None:
            return jsonify({'message': 'Board is not present'}, 404)
        else:
            return make_response(jsonify(board), 200)

    @AdBoardInspector.requires_auth
    def insert_user(self):
        inputs = request.get_json(request)
        user = self.user_schema.load(inputs)
        if len(user.errors) == 0:
            msg, code = self.db.insert_user(user.data)
        else:
            msg, code = user.errors, 400
        return make_response(jsonify(msg), code)

    @AdBoardInspector.requires_auth
    def insert_board(self):
        inputs = request.get_json(request)
        board = self.board_schema.load(inputs)
        if len(board.errors) == 0:
            msg, code = self.db.insert_board(board.data)
        else:
            msg, code = board.errors, 400
        return make_response(jsonify(msg), code)

    @AdBoardInspector.requires_auth
    def like_board(self, board_id):
        board = self.db.get_board(board_id)
        if board is None:
            return make_response(jsonify({'message': 'Board is not present'}), 400)
        else:
            likes = self.db.redis.incrby('likes:board:' + board_id, 1)
            return make_response(jsonify({'status': 'Success', 'count': likes}), 200)

    @AdBoardInspector.requires_auth
    def insert_comment(self, board_id):
        inputs = request.get_json(request)
        comment = self.comment_schema.load(inputs)
        if len(comment.errors) == 0:
            msg, code = self.db.insert_comment(board_id, comment.data)
        else:
            msg, code = comment.errors, 400
        return make_response(jsonify(msg), code)

    @staticmethod
    def get_user_from_header():
        user = request.headers.get('Authorization')
        if user is not None and user.find(':') != -1:
            separator_position = user.find(':')
            author = user[:separator_position]
        return user


a = AdBoardViews(__name__)
a.add_url_rule('/<board_id>', view_func=a.single_board)
a.add_url_rule('/<board_id>/like', view_func=a.like_board, methods=['PUT'])
a.add_url_rule('/<board_id>/insert_comment', view_func=a.insert_comment, methods=['POST'])
a.add_url_rule('/', view_func=a.index)
a.add_url_rule('/', view_func=a.insert_board, methods=['POST'])
a.add_url_rule('/sign_up', view_func=a.insert_user, methods=['POST'])
a.run()
