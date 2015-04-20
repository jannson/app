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
from pypress.models import User, UserCode, Participate
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
            sms_p = sms_privider(self.application, "test")
            if sms_p.check_code(data['mobile'], data['code']):
                sms_p.delete_code(data['mobile'])
                user = User(username=data['username'], mobile=data['mobile'], password=data['password'], role=User.MEMBER)
                user.last_login = datetime.utcnow()
                user.registed = True
                db.session.add(user)
                db.session.commit()

                self.session['user'] = user
                self.session.save()
                self.flash(self._("Welcome, %s" % user.username), "success")

                # redirect
                next_url = form.next.data
                if not next_url:
                    next_url = '/'
                self.redirect(next_url)
            else:
                form.submit.errors.append(u"Register error")

            #print form.errors

        self.render("toway/register.html", form=form)

@route(r'/api/signupall', name='signupall')
class SignupAll(RequestHandler):
    def get(self):
        self.write("error")

    def post(self):
        t = self.get_argument("type")
        mobile = self.get_argument("mobile", "")
        username = self.get_argument("username", "")
        identify = self.get_argument("identify", "")
        password = self.get_argument("password","")
        code = self.get_argument("code")
        act_id = self.get_argument("act_id")

        u = None
        if t == "0":
            user, authenticated = User.query.authenticate(mobile, password)
            if user and authenticated:
                user.last_login = datetime.utcnow() # utcnow
                db.session.commit()
                self.session['user'] = user
                self.session.save()
                self.flash(self._("Welcome back, %s" % user.username), "success")
                self.write("renew")
                u = user
            else:
                self.write("error")
                return

        elif t == "1":
            u = User.query.filter(User.mobile==mobile).first()
            if not u:
                u = User(mobile=mobile, username=username, identify=identify, password="xxxxxx")
                db.session.add(u)
                db.session.commit()
            self.write("ok")

        elif t == "2":
            u = User.query.filter(User.mobile==mobile).first()
            if u:
                u.password = password
                u.username = username
                db.session.commit()
            else:
                u = User(mobile=mobile, username=username, password=password)
            db.session.add(u)
            db.session.commit()

            self.session['user'] = u
            self.session.save()
            self.flash(self._("Welcome back, %s" % u.username), "success")
            self.write("renew")

        try:
            part = Participate(user_id=u.id, act_id=act_id)
            db.session.add(part)
            db.session.commit()
        except:
            pass

