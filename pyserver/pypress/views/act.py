#!/usr/bin/env python
#coding=utf-8

import re
import json
import os
import urllib
import logging
import tornado.web
import tornado.escape

from datetime import datetime
from user_agents import parse

from pypress.views import RequestHandler
from pypress.database import db
from pypress.models import *
from pypress.helpers import generate_random
from pypress.utils.imagelib import Recaptcha
from pypress.extensions.routing import route



@route(r'/createact', name='createact')
class CreateAct(RequestHandler):
    @tornado.web.authenticated
    def get(self):

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
            print "the author is: ", post.author_id

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
        self.render('toway/act_detail.html', post=post, is_login=is_login, sign_text=sign_text, mobile=user_agent.is_mobile)

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

