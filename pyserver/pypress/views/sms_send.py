#!/usr/bin/env python
#coding=utf-8

import re
from datetime import datetime

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import User, UserCode
from pypress.extensions.routing import route
from pypress.extensions.sms import sms_privider
from pypress.extensions.yunpian import tpl_send_sms
from pypress.local_settings import YUNPIAN_APIKEY

mobile_re = re.compile(r'\d{6,20}$')
apikey = YUNPIAN_APIKEY

@route(r'/api/sms_send', name='sms_send')
class Smssend(RequestHandler):
    def get(self):
        self.write("error")

    #def check_xsrf_cookie():
    #http://www.keakon.net/2012/12/03/Tornado%E4%BD%BF%E7%94%A8%E7%BB%8F%E9%AA%8C
    def post(self):
        phone = self.get_argument("phone", default=None)

        if not phone or not mobile_re.match(phone):
            self.write("phone_error")
            return

        user = User.query.filter(User.mobile==phone).first()
        if user:
            self.write("phone_exists")
            return

        x_real_ip = self.request.headers.get("X-Real-IP")
        remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
        sms_p = sms_privider(self.application, "test")
        code = sms_p.gen_code(remote_ip, phone)
        if code:
            print code
            tpl_id = 2
            tpl_value = '#code#=' + str(code) + u'&#company#=突围俱乐部'.encode('utf-8')
            print(tpl_send_sms(apikey, tpl_id, tpl_value, phone))
            self.write("ok")
        else:
            self.write("error")
