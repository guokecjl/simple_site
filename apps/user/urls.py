#!/usr/bin/python
# -*- coding: utf-8 -*-

from .handler import LoginHandler, LogoutHandler, PcGetCaptchaHandler,\
    LoginSuccessHandler
from .ego_login import ReceiveUserInfoHandler, GetLoginResultHandler,\
    GetQrCodeHandler, UserScanHandler

url = [
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/geetest/register", PcGetCaptchaHandler),
    (r"/get_result", GetLoginResultHandler),
    (r"/login_success", LoginSuccessHandler),
    (r"/receive_user_info", ReceiveUserInfoHandler),
    (r"/get_qr_code", GetQrCodeHandler),
    (r"/notify_scan", UserScanHandler)
]