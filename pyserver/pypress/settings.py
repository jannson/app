#!/usr/bin/env python
#coding=utf-8
import os

DEBUG = True
COOKIE_SECRET = 'simple'
LOGIN_URL = '/login'
XSRF_COOKIES = True
THEME_NAME = 'simple'

# default templates and static path settings
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')

# theme path settings
THEME_PATH = os.path.join(os.path.dirname(__file__), 'themes', THEME_NAME)
THEME_TEMPLATE_PATH = os.path.join(THEME_PATH, 'templates')
THEME_STATIC_PATH = os.path.join(THEME_PATH, 'static')

UPLOAD_PATH = os.path.join(STATIC_PATH, 'uploads')

IMAGE_BASE_URL = "http://10.1.1.98:5000/image"
CONTENT_HOST = '127.0.0.1'
CONTENT_PORT = 5000

DEFAULT_LOCALE = 'zh_CN'

REDIS_SERVER = True

# If set to None or 0 the session will be deleted when the user closes the browser.
# If set number the session lives for value days.
PERMANENT_SESSION_LIFETIME = 1 # days

# redis connection config
REDIS_HOST = 'localhost'
REDIS_PORT = 6380
REDIS_DB = 0

try:
    from local_settings import *
except:
    pass

