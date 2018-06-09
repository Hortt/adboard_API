from flask import Flask, url_for, jsonify, request, make_response, Response
import redis
import datetime


a = Flask(__name__)


# @a.route('/boards/<board_id>', methods=['GET'])
def single_board(board_id):
    rredis = redis.Redis('localhost', 6379)
    board_name = rredis.get('board:' + board_id).decode('utf-8')
    if board_name is None:
        return jsonify([{'message': 'Board is not present'}])
    else:
        board_author = rredis.get('author:board:' + board_id).decode('utf-8')
        board_date = datetime.datetime.fromtimestamp(
            int(rredis.get('date_created:' + 'board:' + board_id).decode("utf-8"))
        ).strftime('%Y-%m-%d %H:%M:%S')
        comments = []
    return jsonify({'name': board_name, 'author': board_author, 'date': board_date,
                        'id': board_id, 'comments': comments})


a.add_url_rule('/<board_id>', view_func=single_board)
# a.add_endpoint(endpoint='/<board_id>', endpoint_name='singleboard', handler=a.single_board, methods=['GET'])
a.run()