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


# #### by kidney  ####

raw_html = """
<!DOCTYPE html>
<html ng-app="app">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Angular-xeditable Starter Template</title>
    <!-- Bootstrap 3 css -->
    <link href="//netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css" rel="stylesheet">
    <!-- Angular.js -->
    <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.0.8/angular.min.js"></script>
    <!-- Angular-xeditable -->
    <link href="http://vitalets.github.io/angular-xeditable/dist/css/xeditable.css" rel="stylesheet">
    <script src="http://vitalets.github.io/angular-xeditable/dist/js/xeditable.js"></script>
    <script src="http://code.angularjs.org/1.0.8/angular-mocks.js"></script>
    <style>
        div[ng-app] { margin: 10px; }
        .table {width: 100% }
        form[editable-form] > div {margin: 10px 0;}
    </style>
  </head>
  <body style="padding: 20px">
    <h4>Angular-xeditable Editable row (Bootstrap 3)</h4>
    <div ng-app="app" ng-controller="Ctrl">
       <table class="table table-bordered table-hover table-condensed">
        <tr style="font-weight: bolhttp://jsfiddle.net/NfPcH/93/#forkd">
          <td style="width:35%">Name</td>
          <td style="width:20%">Status</td>
          <td style="width:20%">Group</td>
          <td style="width:25%">Edit</td>
        </tr>
        <tr ng-repeat="user in users">
          <td>
            <!-- editable username (text with validation) -->
            <span editable-text="user.name" e-name="name" e-form="rowform" onbeforesave="checkName($data, user.id)" e-required>
              {{ user.name || 'empty' }}
            </span>
          </td>
          <td>
            <!-- editable status (select-local) -->
            <span editable-select="user.status" e-name="status" e-form="rowform" e-ng-options="s.value as s.text for s in statuses">
              {{ showStatus(user) }}
            </span>
          </td>
          <td>
            <!-- editable group (select-remote) -->
            <span editable-select="user.group" e-name="group" onshow="loadGroups()" e-form="rowform" e-ng-options="g.id as g.text for g in groups">
              {{ showGroup(user) }}
            </span>
          </td>
          <td style="white-space: nowrap">
            <!-- form -->
            <form editable-form name="rowform" onbeforesave="saveUser($data, user.id)" ng-show="rowform.$visible" class="form-buttons form-inline" shown="inserted == user">
              <button type="submit" ng-disabled="rowform.$waiting" class="btn btn-primary">
                save
              </button>
              <button type="button" ng-disabled="rowform.$waiting" ng-click="rowform.$cancel()" class="btn btn-default">
                cancel
              </button>
            </form>
            <div class="buttons" ng-show="!rowform.$visible">
              <button class="btn btn-primary" ng-click="rowform.$show()">edit</button>
              <button class="btn btn-danger" ng-click="removeUser($index)">del</button>
            </div>
          </td>
        </tr>
      </table>

      <button class="btn btn-default" ng-click="addUser()">Add row</button>
    </div>
    <script type="text/javascript">
        var app = angular.module("app", ["xeditable", "ngMockE2E"]);

        app.run(function(editableOptions) {
          editableOptions.theme = 'bs3';
        });

        app.controller('Ctrl', function($scope, $filter, $http) {
         $scope.users = [
            {id: 1, name: 'awesome user1', status: 2, group: 4, groupName: 'admin'},
            {id: 2, name: 'awesome user2', status: undefined, group: 3, groupName: 'vip'},
            {id: 3, name: 'awesome user3', status: 2, group: null}
          ];

          $scope.statuses = [
            {value: 1, text: 'status1'},
            {value: 2, text: 'status2'},
            {value: 3, text: 'status3'},
            {value: 4, text: 'status4'}
          ];

          $scope.groups = [];
          $scope.loadGroups = function() {
            return $scope.groups.length ? null : $http.get('/groups').success(function(data) {
              $scope.groups = data;
            });
          };

          $scope.showGroup = function(user) {
            if(user.group && $scope.groups.length) {
              var selected = $filter('filter')($scope.groups, {id: user.group});
              return selected.length ? selected[0].text : 'Not set';
            } else {
              return user.groupName || 'Not set';
            }
          };

          $scope.showStatus = function(user) {
            var selected = [];
            if(user.status) {
              selected = $filter('filter')($scope.statuses, {value: user.status});
            }
            return selected.length ? selected[0].text : 'Not set';
          };

          $scope.checkName = function(data, id) {
            if (id === 2 && data !== 'awesome') {
              return "Username 2 should be `awesome`";
            }
          };

          $scope.saveUser = function(data, id) {
            //$scope.user not updated yet
            angular.extend(data, {id: id});
            return $http.post('/saveUser', data);
          };

          // remove user
          $scope.removeUser = function(index) {
            $scope.users.splice(index, 1);
          };

          // add user
          $scope.addUser = function() {
            $scope.inserted = {
              id: $scope.users.length+1,
              name: '',
              status: null,
              group: null
            };
            $scope.users.push($scope.inserted);
          };
        });

        // --------------- mock $http requests ----------------------
        app.run(function($httpBackend) {
          $httpBackend.whenGET('/groups').respond([
            {id: 1, text: 'user'},
            {id: 2, text: 'customer'},
            {id: 3, text: 'vip'},
            {id: 4, text: 'admin'}
          ]);

          $httpBackend.whenPOST(/\/saveUser/).respond(function(method, url, data) {
            data = angular.fromJson(data);
            return [200, {status: 'ok'}];
          });
        });
    </script>
  </body>
</html>

"""


from pypress.json_form import JsonForm, _schema

@route(r'/act_apply_test/(.+)', name='act_apply_test')
class ActApplyTest(RequestHandler):
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
        self.render('toway/act_apply.html', act=act, form=form)

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


@route(r'/test_act_create', name='test_act_create')
class CreateActTest(RequestHandler):
    @tornado.web.authenticated
    def get(self):
        p = Permission(RoleNeed("authenticated"))
        p.test(self.identity, 401)

        form = self.forms.ActForm(next=self.get_args('next',''))
        class Form(JsonForm):
            schema = {
                "type": "object",
                "properties": {},
                "required": [],
            }

        json_form = Form(json_data={}, live_schema=_schema)
        #self.render("blog/post.html", form=form)
        self.render("toway/act_test.html", raw_html=raw_html)
        return

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

        self.render("toway/act_test.html", form=form)
        return
