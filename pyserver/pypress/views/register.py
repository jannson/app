#!/usr/bin/env python
#coding=utf-8
"""
    views: account.py
    ~~~~~~~~~~~~~~~~~
    :author: laoqiu.com@gmail.com
"""
from datetime import datetime

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import User, UserCode
from pypress.extensions.routing import route

@route(r'/register', name='register')
class Register(RequestHandler):
    def get(self):
        form = self.forms.RegisterForm(next=self.get_args('next'))
        self.render('toway/register.html', form=form)

    def post(self):
        form = self.forms.RegisterForm(self.request.arguments)
        if form.validate():
            print form.data
            #print form.errors

        self.render("toway/register.html", form=form)
