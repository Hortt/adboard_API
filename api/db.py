import redis
import hashlib
from api.config import config

try:
    db = redis.Redis(config['host'], config['port'])
except ConnectionRefusedError:
    print('Redis connection error')
    exit()


def get_comments(board_id):
    comment_keys = db.keys('commentboard' + board_id + ":*")
    comments = []
    for comment_key in comment_keys:
        comment = db.get(comment_key).decode("utf-8")
        comment_author = db.get('author:' + comment_key.decode("utf-8")).decode("utf-8")
        comments.append({'author': comment_author, 'body': comment})
    return comments


def get_boards():
    boards = db.keys('board:*')
    ads = []
    if boards is not None and len(boards) > 0:
        for board_key in boards:
            board_key = board_key.decode("utf-8")
            board_name = db.get(board_key).decode("utf-8")
            board_author = db.get('author:' + board_key).decode("utf-8")
            board_date = db.get('date_created:' + board_key).decode("utf-8")
            ad = {'name': board_name, 'author': board_author, 'date': board_date,
                  'id': board_key.split(':')[1]}
            ads.append(ad)
    return ads


def insert_user(user_data):
    present_maybe = db.get('user:' + user_data.name)
    if present_maybe is None:
        hash_obj = hashlib.md5(user_data.password.encode('utf-8'))
        db.set('user:' + user_data.name, hash_obj.hexdigest())
        return {'status': 'created'}, 200
    else:
        return {'name': 'The username is already in use'}, 400


def get_board(board_id):
    board_name = db.get('board:' + board_id)
    board = None
    if board_name is not None:
        board_name = board_name.decode("utf-8")
        board_author = db.get('author:board:' + board_id).decode("utf-8")
        board_likes = db.get('likes:board:' + board_id)
        board_likes = 0 if board_likes is None else board_likes.decode("utf-8")
        board_date = db.get('date_created:' + 'board:' + board_id).decode("utf-8")
        comments = get_comments(board_id)
        board = {'name': board_name, 'author': board_author, 'date': board_date,
                 'id': board_id, 'comments': comments, 'likes': board_likes}
    return board


def insert_board(board):
    boards = db.keys('board:*')
    board_key = 'board:' + str(len(boards))
    db.set(board_key, board.name)
    db.set('author:' + board_key, board.author)
    db.set('date_created:' + board_key, board.date)
    return {'status': 'created', 'id': board_key[-1]}, 200


def insert_comment(board_id, comment):
    comments = db.keys('commentboard' + board_id + ":*")
    comment_key = str(len(comments))
    comments_key = 'commentboard{}:{}'.format(board_id, comment_key)
    db.set('author:' + comments_key, comment.author)
    db.set(comments_key, comment.comment)
    return {'status': 'created', 'id': comment_key, 'board_id': board_id}, 202
