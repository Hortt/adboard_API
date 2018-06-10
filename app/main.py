from flask import Flask, jsonify, request, make_response, Response
import redis
from app.models import UserSchema, BoardSchema, CommentSchema
import hashlib


class AdBoardDB:
    def __init__(self, config):
        try:
            self.redis = redis.Redis(config['host'], config['port'])
        except ConnectionRefusedError:
            print('Redis connection error')
            exit()

    def get_comments(self, board_id):
        comment_keys = self.redis.keys('commentboard' + board_id + ":*")
        comments = []
        for comment_key in comment_keys:
            comment = self.redis.get(comment_key).decode("utf-8")
            comment_author = self.redis.get('author:' + comment_key.decode("utf-8")).decode("utf-8")
            comments.append({'author': comment_author, 'body': comment})
        return comments

    def get_boards(self):
        boards = self.redis.keys('board:*')
        ads = []
        if boards is not None and len(boards) > 0:
            for board_key in boards:
                board_key = board_key.decode("utf-8")
                board_name = self.redis.get(board_key).decode("utf-8")
                board_author = self.redis.get('author:' + board_key).decode("utf-8")
                board_date = self.redis.get('date_created:' + board_key).decode("utf-8")
                ad = {'name': board_name, 'author': board_author, 'date': board_date,
                      'id': board_key.split(':')[1]}
                ads.append(ad)
        return ads

    def insert_user(self, user_data):
        present_maybe = self.redis.get('user:' + user_data.name)
        if present_maybe is None:
            hash_obj = hashlib.md5(user_data.password.encode('utf-8'))
            self.redis.set('user:' + user_data.name, hash_obj.hexdigest())
            return {'status': 'created'}, 200
        else:
            return {'name': 'The username is already in use'}, 400

    def get_board(self, board_id):
        board_name = self.redis.get('board:' + board_id)
        board = None
        if board_name is not None:
            board_name = board_name.decode("utf-8")
            board_author = self.redis.get('author:board:' + board_id).decode("utf-8")
            board_likes = self.redis.get('likes:board:' + board_id)
            board_likes = 0 if board_likes is None else board_likes.decode("utf-8")
            board_date = self.redis.get('date_created:' + 'board:' + board_id).decode("utf-8")
            comments = self.get_comments(board_id)
            board = {'name': board_name, 'author': board_author, 'date': board_date,
                     'id': board_id, 'comments': comments, 'likes': board_likes}
        return board

    def insert_board(self, board):
        boards = self.redis.keys('board:*')
        board_key = 'board:'+str(len(boards))
        self.redis.set(board_key, board.name)
        self.redis.set('author:' + board_key, board.author)
        self.redis.set('date_created:' + board_key, board.date)
        return {'status': 'created', 'id': board_key[-1]}, 200

    def insert_comment(self, board_id, comment):
        comments = self.redis.keys('commentboard' + board_id + ":*")
        comment_key = str(len(comments))
        comments_key = 'commentboard' + board_id + ':' + comment_key
        self.redis.set('author:' + comments_key, comment.author)
        self.redis.set(comments_key, comment.comment)
        return {'status': 'created', 'id': comment_key, 'board_id': board_id}, 202

    def get_users(self):
        pass

    def get_user(self, username):
        pass


class EndpointAction(object):
    def __init__(self, action):
        self.action = action
        self.__name__ = action.__name__
        self.response = Response(status=200, headers={})

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)


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

    def index(self):
        boards = self.db.get_boards()
        return make_response(jsonify(boards), 200)

    def single_board(self, board_id):
        board = self.db.get_board(board_id)
        if board is None:
            return jsonify({'message': 'Board is not present'}, 404)
        else:
            return make_response(jsonify(board), 200)

    def insert_user(self):
        inputs = request.get_json(request)
        user = self.user_schema.load(inputs)
        if len(user.errors) == 0:
            msg, code = self.db.insert_user(user.data)
        else:
            msg, code = user.errors, 400
        return make_response(jsonify(msg), code)

    def insert_board(self):
        inputs = request.get_json(request)
        board = self.board_schema.load(inputs)
        if len(board.errors) == 0:
            msg, code = self.db.insert_board(board.data)
        else:
            msg, code = board.errors, 400
        return make_response(jsonify(msg), code)

    def like_board(self, board_id):
        board = self.db.get_board(board_id)
        if board is None:
            return make_response(jsonify({'message': 'Board is not present'}), 400)
        else:
            likes = self.db.redis.incrby('likes:board:'+board_id, 1)
            return make_response(jsonify({'status': 'Success', 'count': likes}), 200)

    def insert_comment(self, board_id):
        inputs = request.get_json(request)
        comment = self.comment_schema.load(inputs)
        if len(comment.errors) == 0:
            msg, code = self.db.insert_comment(board_id, comment.data)
        else:
            msg, code = comment.errors, 400
        return make_response(jsonify(msg), code)


    # def check_auth(self):
    #     header = request.headers.get('Authorization')
    #     if header is not None and header.find(':') != -1:
    #         separator_position = header.find(':')
    #         username = header[:separator_position]
    #         password_hash = hashlib.md5(header[separator_position + 1:].encode('utf-8')).hexdigest()
    #         present_maybe = self.redis.get('user:' + username).decode('utf-8')
    #         if len(present_maybe) > 0 and password_hash == present_maybe:
    #             return True
    #     return False

    def has_cap(self, author, action):
        return True

    @staticmethod
    def get_author_from_header():
        author = request.headers.get('Authorization')
        if author is not None and author.find(':') != -1:
            separator_position = author.find(':')
            author = author[:separator_position]
        return author


a = AdBoardViews(__name__)
a.add_url_rule('/<board_id>', view_func=a.single_board)
a.add_url_rule('/<board_id>/like', view_func=a.like_board, methods=['PUT'])
a.add_url_rule('/<board_id>/insert_comment', view_func=a.insert_comment, methods=['POST'])
a.add_url_rule('/', view_func=a.index)
a.add_url_rule('/', view_func=a.insert_board, methods=['POST'])
a.add_url_rule('/sign_up', view_func=a.insert_user, methods=['POST'])
a.run()
