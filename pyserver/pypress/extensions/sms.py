#!/usr/bin/env python
#coding=utf-8
from random import randint

def sms_privider(app, name):
    return SmsTestPrivider(app.redis)

class SmsTestPrivider(object):

    def __init__(self, redis):
        self.redis = redis

    def gen_code(self, key):
        key_code = self.redis.get(key)
        if key_code:
            return key_code
        code = str(randint(1000,9999))

        cnt_key = key+":cnt"
        cnt = self.redis.incr(cnt_key)
        if cnt == 1:
            self.redis.expire(cnt_key, 60*60*24)
        if cnt > 5:
            return None

        # 10 min
        self.redis.setex(key, code, 60*10)
        return code
    
    def check_code(self, key, code):
        if not key or not code:
            return False

        v = self.redis.get(key)
        if v and v == code:
            return True
        return False
