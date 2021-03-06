#!/usr/bin/env python
#coding=utf-8
import tornado.locale
from datetime import datetime

from pypress.extensions.forms import Form, TextField, PasswordField, SubmitField, \
        TextAreaField, BooleanField, HiddenField, ValidationError, \
        required, regexp, equal_to, email, optional, url, \
        IntegerField, DecimalField, DateTimeField

from pypress.models import User, Post
from pypress.helpers import slugify
from pypress.database import db

USERNAME_RE = r'^[\w.+-]+$'
MOBILE_RE = r'^\d+$'
IDENTIFY_RE = r'^\d{18}$'


def create_forms():

    _forms = {}

    for locale in tornado.locale.get_supported_locales():

        _ = tornado.locale.get(locale).translate
        #logging.info('create forms: %s' % locale)

        is_username = regexp(USERNAME_RE,
                             message=_("You can only use letters, numbers or dashes"))
        is_mobile = regexp(MOBILE_RE,
                             message=u"只能填入手机号")
        is_identify = regexp(IDENTIFY_RE, message=u"身份证填写错误")

        class FormWrapper(object):

            class LoginForm(Form):
                login = TextField(_("Username or email"), validators=[
                                  required(message=\
                                           _("You must provide an email or username"))])

                password = PasswordField(_("Password"))

                remember = BooleanField(_("Remember me"))

                next = HiddenField()

                submit = SubmitField(_("Login"))


            class SignupForm(Form):
                username = TextField(_("Username"), validators=[
                                     required(message=_("Username required")),
                                     is_username])

                nickname = TextField(_("Nickname"), validators=[
                                     required(message=_("Nickname required"))])

                password = PasswordField(_("Password"), validators=[
                                         required(message=_("Password required"))])

                password_again = PasswordField(_("Password again"), validators=[
                                               equal_to("password", message=\
                                                        _("Passwords don't match"))])

                email = TextField(_("Email"), validators=[
                                  required(message=_("Email required")),
                                  email(message=_("A valid email is required"))])

                code = TextField(_("Signup Code"))

                next = HiddenField()

                submit = SubmitField(_("Signup"))

                def validate_username(self, field):
                    user = User.query.filter(User.username.like(field.data)).first()
                    if user:
                        raise ValidationError, _("This username is taken")

                def validate_email(self, field):
                    user = User.query.filter(User.email.like(field.data)).first()
                    if user:
                        raise ValidationError, _("This email is taken")


            class RecoverPasswordForm(Form):
                email = TextField(_("Your email address"), validators=[
                                  email(message=_("A valid email is required"))])

                submit = SubmitField(_("Find password"))


            class ChangePasswordForm(Form):
                password_old = PasswordField(_("Password"), validators=[
                                         required(message=_("Password is required"))])

                password = PasswordField(_("New Password"), validators=[
                                         required(message=_("New Password is required"))])

                password_again = PasswordField(_("Password again"), validators=[
                                               equal_to("password", message=\
                                                        _("Passwords don't match"))])

                submit = SubmitField(_("Save"))


            class DeleteAccountForm(Form):
                recaptcha = TextField(_("Recaptcha"))

                submit = SubmitField(_("Delete"))


            class PostForm(Form):
                title = TextField(_("Title"), validators=[
                                  required(message=_("Title required"))])

                slug = TextField(_("Slug"))

                content = TextAreaField(_("Content"), validators=[
                                        required(message=_("Content required"))])

                tags = TextField(_("Tags"), validators=[
                                  required(message=_("Tags required"))])

                submit = SubmitField(_("Save"))

                next = HiddenField()

                def validate_slug(self, field):
                    if len(field.data) > 50:
                        raise ValidationError, _("Slug must be less than 50 characters")
                    slug = slugify(field.data) if field.data else slugify(self.title.data)[:50]
                    posts = Post.query.filter_by(slug=slug)
                    if self.obj:
                        posts = posts.filter(db.not_(Post.id==self.obj.id))
                    if posts.count():
                        error = _("This slug is taken") if field.data else _("Slug is required")
                        raise ValidationError, error


            class CommentForm(Form):
                email = TextField(_("Email"), validators=[
                                  required(message=_("Email required")),
                                  email(message=_("A valid email is required"))])

                nickname = TextField(_("Nickname"), validators=[
                                  required(message=_("Nickname required"))])

                website = TextField(_("Website"), validators=[
                                    optional(),
                                    url(message=_("A valid url is required"))])

                comment = TextAreaField(_("Comment"), validators=[
                                        required(message=_("Comment required"))])

                captcha = TextField(_("Captcha"), validators=[
                                    required(message=_("Captcha required"))])

                submit = SubmitField(_("Add comment"))
                cancel = SubmitField(_("Cancel"))


            class LinkForm(Form):
                name = TextField(_("Site name"), validators=[
                                  required(message=_("Site name required"))])

                link = TextField(_("link"), validators=[
                                url(message=_("A valid url is required"))])

                email = TextField(_("Email"), validators=[
                                email(message=_("A valid email is required"))])

                logo = TextField(_("Logo"), validators=[
                                optional(),
                                url(message=_("A valid url is required"))])

                description = TextAreaField(_("Description"))

                submit = SubmitField(_("Save"))

            class RegisterForm(Form):
                mobile = TextField(_("Mobile"), validators=[
                                     required(message=_("Mobile required")),
                                     is_mobile], default=u"")

                username = TextField(_("Username"), validators=[
                                     required(message=_("Username required")),
                                     is_username], default=u"")

                password = PasswordField(_("Password"), validators=[
                                         required(message=_("Password required"))], default=u"")

                code = TextField(_("Code"), default=u"")

                next = HiddenField(default=u"")

                submit = SubmitField(_("Register"), default=u"")

                def validate_username(self, field):
                    user = User.query.filter(User.username.like(field.data)).first()
                    if user:
                        raise ValidationError, u"用户名已经存在"

                def validate_mobile(self, field):
                    user = User.query.filter(User.mobile == field.data).first()
                    if user:
                        raise ValidationError, u"手机号已经被注册"

            class ActForm(Form):
                title = TextField(_("Title"), default=u"", validators=[
                                  required(message=_("Title required"))])

                slug = TextField(_("Slug"), default=u"")

                content = TextAreaField(_("Content"), validators=[
                                        required(message=_("Content required"))])

                tags = TextField(_("Tags"), validators=[
                                  required(message=_("Tags required"))], default=u"")

                start_date = DateTimeField(_("StartDate"), default=datetime.now())
                finish_date = DateTimeField(_("FinishDate"), default=datetime.now())
                sign_start_date = DateTimeField("SignupStartDate", default=datetime.now())
                sign_finish_date = DateTimeField("SignupEndDate", default=datetime.now())
                city_name = TextField(_("CityName"), default=u"深圳")
                location = TextField(_("Location"), default=u"")
                limit_num = IntegerField(_("LimitNum"), default=0)
                pay_count = IntegerField(_("PayCount"), default=0)

                linkinfo = TextField(default=u"")

                photo = TextField(default=u"")
                latitude = DecimalField(default=22.5314898650969)
                longitude = DecimalField(default=113.915101289749)
                zoomlevel = IntegerField(default=13)

                submit = SubmitField(_("Save"))

                next = HiddenField()

                def validate_slug(self, field):
                    if len(field.data) > 50:
                        raise ValidationError, _("Slug must be less than 50 characters")
                    slug = slugify(field.data) if field.data else slugify(self.title.data)[:50]
                    posts = Post.query.filter_by(slug=slug)
                    if self.obj:
                        posts = posts.filter(db.not_(Post.id==self.obj.id))
                    if posts.count():
                        error = _("This slug is taken") if field.data else _("Slug is required")
                        raise ValidationError, error

            class ActApplyForm(Form):
                mobile = TextField(_("Mobile"), validators=[
                                     required(message=_("Mobile required")),
                                     is_mobile], default=u"")

                realname = TextField(_("RealName"), default=u"")

                nickname = TextField(_("NickName"), default=u"")

                #identify = TextField(_("Identity"), validators=[
                #                     required(message=u"身份证填写错误") ,is_identify], default=u"")

                code = PasswordField(_("Code"), validators=[
                                         required(message=_("Auth code required"))], default=u"")

                act_id = HiddenField(default=u"")
                next = HiddenField(default=u"")

                submit = SubmitField(_("Register"), default=u"")

        _forms[locale] = FormWrapper

    return _forms

