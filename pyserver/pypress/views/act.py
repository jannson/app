#!/usr/bin/env python
#coding=utf-8

import re
import json
import os
import urllib
import logging
import tornado.web
import tornado.escape

from datetime import datetime, timedelta
from user_agents import parse

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import *
from pypress.helpers import generate_random
from pypress.utils.imagelib import Recaptcha
from pypress.extensions.routing import route
from pypress.extensions.sms import sms_privider
from pypress.extensions.permission import Permission, RoleNeed


@route(r'/act_create', name='act_create')
class CreateAct(RequestHandler):
    @tornado.web.authenticated
    def get(self):
        p = Permission(RoleNeed("authenticated"))
        p.test(self.identity, 401)

        form = self.forms.ActForm(next=self.get_args('next',''))
        #self.render("blog/post.html", form=form)
        self.render("toway/act.html", form=form)
        return

    @tornado.web.authenticated
    def post(self):

        form = self.forms.ActForm(self.request.arguments)

        if form.validate():

            post = Act(author_id=self.current_user.id)
            form.populate_obj(post)
            post.author_id = self.get_current_user().id

            db.session.add(post)
            db.session.commit()

            # redirect
            next_url = form.next.data
            if not next_url:
                next_url = post.url
            self.redirect(next_url)
            return

        self.render("toway/act.html", form=form)
        return

#pip install pyyaml ua-parser user-agents
@route(r'/act/(.+)', name='act_view')
class ActDetail(RequestHandler):
    def get(self, slug):
        ua_string = self.request.headers.get('user-agent', '')
        user_agent = parse(ua_string)
        post = Post.query.get_by_slug(slug)
        user = self.get_current_user()
        sign_text = u"报名"
        is_login = False
        if user:
            is_login = True
            p = Participate.query.filter_by(user_id=user.id).filter_by(act_id=post.id).first()
            if p:
                sign_text = u"报名成功"

        if len(post.linkinfo) == 0:
            html = 'toway/act_simple.html'
        else:
            html = 'toway/act_brief.html'
        self.render(html, post=post, is_login=is_login, sign_text=sign_text, mobile=user_agent.is_mobile)

@route(r'/api/parts/(\d+)', name='api_parts')
class ApiParts(RequestHandler):
    def get(self, act_id):
        parts = Participate.query.filter(Participate.act_id==act_id)
        users = [rel.user for rel in parts]
        self.render('toway/api_parts.html', parts=users)

@route(r'/api/logon_sign', name='logon_sign')
class LogonSign(RequestHandler):
    def get(self):
        self.write("error")

    def post(self):
        user = self.get_current_user()
        if user:
            act_id = self.get_argument("act_id")
            user_id = user.id
            try:
                part = Participate(user_id=user_id, act_id=act_id)
                db.session.add(part)
                db.session.commit()
            except:
                pass
            self.write('ok')
        else:
            self.write('error')

@route(r'/act_apply2/(.+)', name='act_apply2')
class ActApply2(RequestHandler):
    def get(self, slug):
        #act = Act.query.get_or_404(act_id)
        act = Post.query.get_by_slug(slug)
        act_id = act.id
        form = self.forms.ActApplyForm(next=self.get_args('next'))
        form.act_id.process_data(act.id)
        if len(act.linkinfo) == 0:
            form.next.process_data(act.url)
        else:
            form.next.process_data(act.linkinfo)
        #self.render('toway/act_apply.html', act=act, form=form)
        self.render('toway/act-zz.html', act=act, form=form)

    def post(self, slug):
        form = self.forms.ActApplyForm(self.request.arguments)
        if form.validate():
            data = form.data
            mobile = data["mobile"].strip()
            realname = data["realname"].strip()
            nickname = data["nickname"].strip()
            identify = data["identify"].strip()
            code = data["code"].strip()
            user = User.query.filter(User.mobile==mobile).first()

            #check
            while True:
                pass_ok = False
                if not user:
                    user = User(mobile=mobile, realname=realname, nickname=nickname, identify=identify)
                else:
                    #user exists, check password
                    pass_ok = user.check_password(code)

                    if realname:
                        user.realname = realname
                        user.nickname = realname
                    if identify:
                        user.identify = identify
                    if nickname:
                        user.nickname = nickname

                if not user.realname:
                    form.submit.errors.append(u"RealName is empty")
                    break
                if not user.identify:
                    form.submit.errors.append(u"Identify is empty")
                    break

                if not pass_ok:
                    sms_p = sms_privider(self.application, "test")
                    code_ok = sms_p.check_code(mobile, code)
                    sms_p.delete_code(mobile)
                    if not code_ok:
                        form.submit.errors.append(u"The code is error")
                        break

                    #set password
                if not user.registed:
                    user.password = code
                    user.validate_till = datetime.utcnow() + timedelta(days=15)

                db.session.add(user)
                db.session.commit()

                act_id = int(data["act_id"])
                user_id = user.id
                p = Participate.query.filter_by(user_id=user.id).filter_by(act_id=act_id).first()
                if not p:
                    try:
                        part = Participate(user_id=user_id, act_id=act_id)
                        db.session.add(part)
                        db.session.commit()
                    except:
                        pass

                self.session['user'] = user
                self.session.save()
                self.flash(self._("%s" % user.nickname), "success apply !")

                next_url = form.next.data
                path = self.reverse_url('act_apply_ok', next_url)
                self.redirect(path)

                #break while True
                break

        act = Post.query.get_by_slug(slug)
        #act = Act.query.get_or_404(act_id)
        self.render("toway/act_apply.html", act=act, form=form)

@route(r'/act_apply/(.+)', name='act_apply')
class ActApply(RequestHandler):
    def get(self, slug):
        act = Post.query.get_by_slug(slug)
        act_id = act.id
        form = self.forms.ActApplyForm(next=self.get_args('next'))
        form.act_id.process_data(act.id)
        if len(act.linkinfo) == 0:
            form.next.process_data(act.url)
        else:
            form.next.process_data(act.linkinfo)
        self.render('toway/act-zz.html', act=act, form=form)

    def post(self, slug):
        form = self.forms.ActApplyForm(self.request.arguments)
        if form.validate():
            data = form.data
            mobile = data["mobile"].strip()
            realname = data["realname"].strip()
            nickname = data["nickname"].strip()
            code = data["code"].strip()
            user = User.query.filter(User.mobile==mobile).first()

            act_id = int(data["act_id"])
            act = Post.query.get(act_id)
            key_set = [field["input_name"] for field in act.extras]
            key_value = {}
            args = self.request.arguments
            for k in key_set:
                if k in args and len(args[k]) > 0:
                    key_value[k] = args[k]

            #check
            while True:
                pass_ok = False
                if not user:
                    user = User(mobile=mobile, realname=realname, nickname=nickname)
                else:
                    #user exists, check password
                    pass_ok = user.check_password(code)

                    extra = user.extras
                    extra.update(**key_value)
                    user.extra_info = json.dumps(extra)

                    if realname:
                        user.realname = realname
                        user.nickname = realname
                    if nickname:
                        user.nickname = nickname

                if not user.realname:
                    form.submit.errors.append(u"RealName is empty")
                    break

                if not pass_ok:
                    sms_p = sms_privider(self.application, "test")
                    code_ok = sms_p.check_code(mobile, code)
                    sms_p.delete_code(mobile)
                    if not code_ok:
                        form.submit.errors.append(u"The code is error")
                        break

                    #set password
                if not user.registed:
                    user.password = code
                    user.validate_till = datetime.utcnow() + timedelta(days=15)

                db.session.add(user)
                db.session.commit()

                user_id = user.id
                p = Participate.query.filter_by(user_id=user.id).filter_by(act_id=act_id).first()
                if not p:
                    try:
                        part = Participate(user_id=user_id, act_id=act_id)
                        db.session.add(part)
                        db.session.commit()
                    except:
                        pass

                self.session['user'] = user
                self.session.save()
                self.flash(self._("%s" % user.nickname), "success apply !")

                next_url = form.next.data
                path = self.reverse_url('act_apply_ok', next_url)
                self.redirect(path)

                #break while True
                break

        act = Post.query.get_by_slug(slug)
        self.render("toway/act-zz.html", act=act, form=form)

@route(r'/act_apply_ok/(.+)', name='act_apply_ok')
class ActApplyOk(RequestHandler):
    def get(self, next_url):
        self.write(u"报名成功! <h3><a href='%s'>返回</a></h3>" % next_url)
