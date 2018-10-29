# coding: utf-8

import logging

import tornado.gen
import tornado.web
from tornado.gen import coroutine
from tornado.web import authenticated
from geetest import GeetestLib

from base_handler import BaseRequestHandler
from config import GT_ID, GT_KEY


class LoginHandler(BaseRequestHandler):
    @coroutine
    def get(self):
        self.set_cookie('_xsrf', self.xsrf_token)
        self.render("user_login.html")

    @coroutine
    def post(self):
        try:
            self.write_response({})
        except Exception as e:
            logging.exception(e)
            msg = '登录出现异常，请稍后重试'
            self.write_response('', 0, msg)


class LogoutHandler(BaseRequestHandler):
    """
    退出登陆认证
    """
    @authenticated
    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        self.clear_all_cookies()
        self.redirect("/user/login")


class LoginSuccessHandler(BaseRequestHandler):
    @coroutine
    def get(self):
        self.write_response()


class PcGetCaptchaHandler(BaseRequestHandler):
    @tornado.gen.coroutine
    def get(self):
        user_id = 'test'
        try:
            gt = GeetestLib(GT_ID, GT_KEY)
            status = gt.pre_process(user_id)
            response_str = gt.get_response_str()
            self.write(response_str)
        except Exception as e:
            logging.exception(e)
            self.write('对不起，请求验证码异常')