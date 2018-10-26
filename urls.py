#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from apps.user.urls import url as user_url
from config import DEBUG

settings = {
    "cookie_secret": "hdbfajerfny43927p5yta35br69p7456",
    "login_url": "/user/login",
    "xsrf_cookies": False,
    'gzip': True,
    'debug': DEBUG,
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    'static_path': os.path.join(os.path.dirname(__file__), "static"),
    'websocket_ping_interval': 30,  # 每隔30秒检查websocket连接
}

raw_url = [
    (r"/user", user_url),
]

url = []
for i in raw_url:
    for j in i[1]:
        url.append((r"%s" % i[0] + j[0], j[1]))