#!/usr/bin/env python
#coding=utf-8

import json
import os
import urllib
import logging
import tornado.web
import tornado.escape

from datetime import datetime

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

@route(r'/act/(\d{4})/(\d{1,2})/(\d{1,2})/(.+)', name='act_view')
class ActDetail(RequestHandler):
    def get(self, year, month, day, slug):
        post = Post.query.get_by_slug(slug)

        date = (post.created_date.year,
                post.created_date.month,
                post.created_date.day)

        if (int(year), int(month), int(day)) != date:
            raise tornado.web.HTTPError(404)

        #self.render("blog/view.html", post=post, form=self.forms.CommentForm())
        self.render('toway/act_detail.html', post=post)

@route(r'/api/logon_sign', name='logon_sign')
class LogonSign(RequestHandler):
    def get(self):
        self.write("error")

    def post(self):
        act_id = self.get_argument("act_id")
        user_id = self.get_current_user().id
        part = Participate(user_id=user_id, act_id=act_id)
        db.session.add(part)

