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
            
            post = Post(author_id=self.current_user.id)
            form.populate_obj(post)

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
