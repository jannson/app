#!/usr/bin/env python
#coding=utf-8

from datetime import datetime

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import User, UserCode
from pypress.extensions.routing import route
from pypress.extensions.sms import sms_privider

@route(r'/api/sms_send', name='sms_send')
class Smssend(RequestHandler):
    def get(self):
        self.write("error")

    #def check_xsrf_cookie():
    #http://www.keakon.net/2012/12/03/Tornado%E4%BD%BF%E7%94%A8%E7%BB%8F%E9%AA%8C
    def post(self):
        print 'hear'
        print self.request.body

        x_real_ip = self.request.headers.get("X-Real-IP")
        remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
        sms_p = sms_privider(self.application, "test")
        code = sms_p.gen_code(remote_ip)
        if code:
            self.write("ok")
        else:
            self.write("error")
