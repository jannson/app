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
from pypress.extensions.sms import sms_privider

@route(r'/register', name='register')
class Register(RequestHandler):
    def get(self):
        #x_real_ip = self.request.headers.get("X-Real-IP")
        #remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
        #sms_p = sms_privider(self.application, "test")
        #print remote_ip, sms_p.send_code(remote_ip, '5564')

        form = self.forms.RegisterForm(next=self.get_args('next'))
        #print form.mobile.data
        self.render('toway/register.html', form=form)

    def post(self):
        form = self.forms.RegisterForm(self.request.arguments)
        if form.validate():
            data = form.data
            print data
            #print form.errors

        self.render("toway/register.html", form=form)
