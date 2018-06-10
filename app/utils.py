import redis, hashlib
from functools import wraps
from flask import request, jsonify, make_response


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
        board_key = 'board:' + str(len(boards))
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

    def __call__(self, *args, **kwargs):
        # here we can add middlewares
        return self.action(*args, **kwargs)


class AdBoardInspector():

    @classmethod
    def requires_auth(cls, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = AdBoardInspector.check_auth()
            if not auth:
                return make_response(jsonify({'message': 'Authorization is required'}), 401)
            return f(*args, **kwargs)

        return decorated

    @staticmethod
    def check_auth():
        header = request.headers.get('Authorization')
        if header is not None and header.find(':') != -1:
            db = AdBoardDB({'host': 'localhost', 'port': 6379})
            separator_position = header.find(':')
            username = header[:separator_position]
            password_hash = hashlib.md5(header[separator_position + 1:].encode('utf-8')).hexdigest()
            present_maybe = db.redis.get('user:' + username).decode('utf-8')
            if len(present_maybe) > 0 and password_hash == present_maybe:
                return True
        return False
