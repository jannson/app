#!/usr/bin/env python
#coding=utf-8
"""
    models: users.py
    ~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""

import hashlib
import json
from datetime import datetime

import tornado.web

from pypress.extensions.sqlalchemy import BaseQuery
from pypress.extensions.permission import Permission, RoleNeed, UserNeed
from pypress.extensions.cache import cached_property
from pypress.permissions import admin
from pypress.database import db


__all__ = ['User', 'UserCode', 'Tweet', ]


class UserQuery(BaseQuery):

    def authenticate(self, login, password):

        user = self.filter(db.or_(User.username==login,
                                  User.mobile==login)).filter(User.registed==True).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    def search(self, key):
        query = self.filter(db.or_(User.mobile==key,
                                   User.nickname.ilike('%'+key+'%'),
                                   User.username.ilike('%'+key+'%')))
        return query

    def get_by_username(self, username):
        user = self.filter(User.username==username).first()
        if user is None:
            raise tornado.web.HTTPError(404)
        return user


class User(db.Model):

    __tablename__ = 'users'

    query_class = UserQuery

    PER_PAGE = 50
    TWEET_PER_PAGE = 30

    MEMBER = 100
    MODERATOR = 200
    ADMIN = 300

    id = db.Column(db.Integer, primary_key=True)
    #1:Shenzhen
    city_id = db.Column('city_id', db.Integer, db.ForeignKey('city.id'), default=1)
    username = db.Column(db.String(20), unique=True, nullable=True)
    nickname = db.Column(db.String(20), nullable=True)
    realname = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    mobile = db.Column(db.String(20), unique=True, nullable=True)
    _password = db.Column("password", db.String(80), nullable=False)
    identify = db.Column(db.String(50), nullable=True)
    avatar = db.Column(db.String(200))
    extra_info = db.Column(db.UnicodeText())

    [MALE, FEMALE] = range(2)
    sex = db.Column(db.Integer(), default=MALE)

    role = db.Column(db.Integer, default=MEMBER)
    activation_key = db.Column(db.String(40))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    validate_till = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    block = db.Column(db.Boolean, default=False)
    registed = db.Column(db.Boolean, default=False)

    class Permissions(object):

        def __init__(self, obj):
            self.obj = obj

        @cached_property
        def edit(self):
            return Permission(UserNeed(self.obj.id)) & admin


    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

    def __str__(self):
        return "User: %s" % self.nickname

    def __repr__(self):
        return "<%s>" % self

    @cached_property
    def permissions(self):
        return self.Permissions(self)

    @cached_property
    def provides(self):
        needs = [UserNeed(self.id)]

        if self.registed:
            needs.append(RoleNeed('authenticated'))

        if self.is_moderator:
            needs.append(RoleNeed('moderator'))

        if self.is_admin:
            needs.append(RoleNeed('admin'))

        return needs

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = hashlib.md5(password).hexdigest()

    password = db.synonym("_password",
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self,password):
        if self.password is None:
            return False
        return self.password == hashlib.md5(password).hexdigest()

    @property
    def is_moderator(self):
        return self.role >= self.MODERATOR

    @property
    def is_admin(self):
        return self.role >= self.ADMIN

    @cached_property
    def base_info(self):
        return set(["username", "nickname", "mobile"])

    @property
    def extras(self):
        if self.extra_info:
            return json.loads(self.extra_info)
        return {}

    @property
    def json(self):
        return dict(id=self.id,
                    username=self.username,
                    nickname=self.nickname,
                    mobile=self.mobile,
                    email=self.email,
                    is_admin=self.is_admin,
                    is_moderator=self.is_moderator,
                    last_login=self.last_login)


class UserCode(db.Model):

    __tablename__ = 'usercode'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    role = db.Column(db.Integer, default=User.MEMBER)

    def __init__(self, *args, **kwargs):
        super(UserCode, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<%s>" % self


class Tweet(db.Model):

    __tablename__ = 'tweets'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey(User.id, ondelete='CASCADE'),
                        nullable=False,
                        unique=True)

    server = db.Column(db.String(50))
    token = db.Column(db.String(50))
    token_secret = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Tweet, self).__init__(*args, **kwargs)

    def __str__(self):
        return "Tweet: %s" % self.id

    def __repr__(self):
        return "<%s>" % self


User.tweets = db.relation(Tweet, backref="user")

# to do ...
User.weibo = None
User.douban = None
User.qq = None

