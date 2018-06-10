from marshmallow import fields, validate, Schema, post_load, ValidationError
from datetime import datetime, timezone
from flask import Blueprint

mod = Blueprint('models', __name__)


class User(object):
    def __init__(self, name, password, confirm):
        self.name = name
        self.password = password
        self.confirm = confirm


class UserSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=20))
    password = fields.String(required=True, validate=validate.Length(min=1, max=20))
    confirm = fields.String(required=True, validate=validate.Length(min=1, max=20))

    @post_load()
    def create_user(self, data):
        if data['password'] != data['confirm']:
            raise ValidationError('Paswords match error', ['confirm'])
        return User(**data)


class Board(object):
    def __init__(self, name, author, date):
        self.name = name
        self.author = author
        self.date = date


class BoardSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=10, max=50))
    author = fields.String(required=True, validate=validate.Length(min=1, max=20))
    date = fields.DateTime(required=False)

    @post_load()
    def create_board(self, data):
        data['date'] = datetime.now(tz=timezone.utc)
        return Board(**data)


class Comment(object):
    def __init__(self, comment, author):
        self.comment = comment
        self.author = author


class CommentSchema(Schema):
    comment = fields.String(required=True, validate=validate.Length(min=10, max=255))
    author = fields.String(required=True, validate=validate.Length(min=1, max=30))

    @post_load()
    def create_comment(self, data):
        return Comment(**data)
