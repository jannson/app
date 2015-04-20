#!/usr/bin/env python
#coding=utf-8
from random import randint

def sms_privider(app, name):
    return SmsTestPrivider(app.redis)

class SmsTestPrivider(object):

    def __init__(self, redis):
        self.redis = redis

    def gen_code(self, ip, phone):
        key_code = self.redis.get(phone)
        if key_code:
            return key_code
        code = str(randint(100000,999999))

        cnt_key = ip+":cnt"
        cnt = self.redis.incr(cnt_key)
        if cnt == 1:
            self.redis.expire(cnt_key, 60*60*24)
        if cnt > 5:
            return None

        # 10 min
        self.redis.setex(phone, code, 60*10)

        return code

    def check_code(self, phone, code):
        if not phone or not code:
            return False

        v = self.redis.get(phone)
        if v and v == code:
            return True
        return False

    def delete_code(self, phone):
        self.redis.delete(phone)
