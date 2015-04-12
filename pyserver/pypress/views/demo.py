#!/usr/bin/env python
#coding=utf-8
"""
    views: account.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
from datetime import datetime
import cPickle as pickle

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import User, UserCode
from pypress.extensions.routing import route

@route(r'/logindemo', name='logindemo')
class LoginDemo(RequestHandler):
    def get(self):
        print "hear"
        self.render('toway/logindemo.html')
        return
