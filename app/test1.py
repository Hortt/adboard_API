from flask import Flask, jsonify, request, make_response, Response
import redis
import datetime
import time
import hashlib


class EndpointAction(object):
    def __init__(self, action):
        self.action = action
        self.__name__ = action.__name__
        self.response = Response(status=200, headers={})

    def __call__(self, *args):
        return self.action()


class FlaskAppWrapper(object):
    app = None

    def __init__(self, name):
        self.app = Flask(name)
        self.redis = self.redis = redis.Redis('localhost', 6379)

    def run(self):
        self.app.run()

    def add_url_rule(self, rule, endpoint=None, view_func=None, provide_automatic_options=None, **options):

        if view_func is not None:
            view_func = EndpointAction(view_func)
        self.app.add_url_rule(rule, endpoint, view_func, provide_automatic_options, **options)

    def index(self):
        if not self.check_auth():
            return make_response('Authorization is required', 401)
        boards = self.redis.keys('board:*')
        ads = []
        if boards is not None and len(boards) > 0:
            for board_key in boards:
                board_name = self.redis.get(board_key).decode("utf-8")
                board_author = self.redis.get('author:' + board_key.decode("utf-8")).decode("utf-8")
                board_date = datetime.datetime.fromtimestamp(
                    int(self.redis.get('date_created:' + board_key.decode("utf-8")).decode("utf-8"))
                ).strftime('%Y-%m-%d %H:%M:%S')
                ad = {'name': board_name, 'author': board_author, 'date': board_date,
                      'id': board_key.decode('utf-8').split(':')[1]}
                ads.append(ad)
        return make_response(jsonify(ads), 200)

    def single_board(self, board_id):
        if not self.check_auth():
            return make_response('Authorization is required', 401)
        board_name = self.redis.get('board:' + board_id).decode('utf-8')
        if board_name is None:
            return jsonify([{'message': 'Board is not present'}], 404)
        else:
            board_author = self.redis.get('author:board:' + board_id).decode('utf-8')
            board_date = datetime.datetime.fromtimestamp(
                int(self.redis.get('date_created:' + 'board:' + board_id).decode("utf-8"))
            ).strftime('%Y-%m-%d %H:%M:%S')
            comments = self.get_comments(board_id)
        return make_response(jsonify({'name': board_name, 'author': board_author, 'date': board_date,
                                      'id': board_id, 'comments': comments}), 200)

    def get_comments(self, board_id):
        comment_keys = self.redis.keys('commentboard' + board_id + ":*")
        comments = []
        for comment_key in comment_keys:
            comment = self.redis.get(comment_key).decode("utf-8")
            comment_author = self.redis.get('author:' + comment_key.decode("utf-8")).decode("utf-8")
            comments.append({'author': comment_author, 'body': comment})
        return comments

    def insert_user(self):
        inputs = request.get_json(request)
        username = inputs['username']
        password = inputs['password']
        confirm_password = inputs['confirm_password']
        if len(username) < 20 and 3 < len(password) < 20 and password == confirm_password:
            present_maybe = self.redis.get('user:' + username)
            if present_maybe is None or len(present_maybe) == 0:
                hashobj = hashlib.md5(password.encode('utf-8'))
                self.redis.set('user:' + username, hashobj.hexdigest())
                msg = {'status': 'created'}
                code = 200
            else:
                msg = 'Pick another username, the current one is in use'
                code = 409
        else:
            msg = 'Wrong input'
            code = 400
        return make_response(jsonify(msg), code)

    def insert_board(self):
        if not self.check_auth():
            return make_response('Authorization is required', 401)
        inputs = request.get_json(request)
        name = inputs['name']
        author = inputs['author']
        boards = self.redis.keys('board:*')
        if len(boards) == 0:
            board_key = 'board:1'
        else:
            boards.sort()
            max_key = boards[-1].decode('utf-8') if len(boards) > 1 else boards[0].decode('utf-8')
            prefix, num = max_key.split(':')
            board_key = 'board:' + str(int(num) + 1)
        self.redis.set(board_key, name)
        self.redis.set('author:' + board_key, author)
        self.redis.set('date_created:' + board_key, int(time.time()))
        return make_response(board_key.capitalize() + ' Created', 202)

    def update_board(self, board_id):
        if not self.check_auth():
            return make_response('Authorization is required', 401)
        inputs = request.get_json(request)
        action = inputs['action']
        board = self.redis.get('board:' + board_id)
        if board is None or len(board) == 0:
            return make_response({'status': 'failed', 'message': 'Board ID: ' + board_id + ' is not present '}, 403)
        elif self.has_cap(self.get_author_from_header(), action):
            return make_response(
                {'status': 'updated', 'board_id': board_id, 'likes': self.redis.incr('likes:board:' + board_id, 1)},
                202)
        else:
            return make_response({'status': 'failed', 'board_id': board_id, 'message': 'forbidden to ' + action}, 403)

    def insert_comment(self, board_id):
        if not self.check_auth():
            return make_response('Authorization is required', 401)
        inputs = request.get_json(request)
        comment = inputs['comment']
        author = inputs['author']
        action = 'comment'
        if not self.has_cap(self.get_author_from_header(), action):
            return make_response({'status': 'failed', 'board_id': board_id, 'message': 'forbidden to ' + action}, 403)
        comments = self.redis.keys('commentboard' + board_id + ":*")
        if len(comments) == 0:
            redis_key = '1'
        else:
            comments.sort()
            max_key = comments[-1].decode('utf-8') if len(comments) > 1 else comments[0].decode('utf-8')
            prefix, num = max_key.split(':')
            redis_key = str(int(num) + 1)
        comments_key = 'commentboard' + board_id + ':' + redis_key
        self.redis.set('author:' + comments_key, author)
        self.redis.set(comments_key, comment)
        return make_response(jsonify({'status': 'created', 'comment_id': redis_key, 'board_id': board_id}), 202)

    def check_auth(self):
        header = request.headers.get('Authorization')
        if header is not None and header.find(':') != -1:
            separator_position = header.find(':')
            username = header[:separator_position]
            password_hash = hashlib.md5(header[separator_position + 1:].encode('utf-8')).hexdigest()
            present_maybe = self.redis.get('user:' + username).decode('utf-8')
            if len(present_maybe) > 0 and password_hash == present_maybe:
                return True
        return False

    def has_cap(self, author, action):
        return True

    @staticmethod
    def get_author_from_header():
        author = request.headers.get('Authorization')
        if author is not None and author.find(':') != -1:
            separator_position = author.find(':')
            author = author[:separator_position]
        return author


a = FlaskAppWrapper('wrap')
a.app.add_url_rule('/<board_id>', view_func=a.single_board)
a.app.add_url_rule('/<board_id>', view_func=a.update_board, methods=['PUT'])
a.app.add_url_rule('/<board_id>/insert_comment', view_func=a.insert_comment, methods=['POST'])
a.app.add_url_rule('/', view_func=a.index)
a.app.add_url_rule('/', view_func=a.insert_board, methods=['POST'])

# @todo: all others should be refactored and called like this one
a.add_url_rule('/sign_up', view_func=a.insert_user, methods=['POST'])
a.run()
