#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
import tornado.ioloop
import tornado.web

from config import BIND_IP, BIND_PORT, LOG_DIR, LOG_FILE
from urls import url, settings


def make_app():
    return tornado.web.Application(url, **settings)

if not os.path.exists(LOG_DIR + '/' + LOG_FILE):
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    os.mknod(LOG_DIR + '/' + LOG_FILE)

log_config = dict(
    level=logging.WARNING,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=LOG_DIR + '/' + LOG_FILE,
    filemode='a'
)

logging.basicConfig(**log_config)


if __name__ == "__main__":
    app = make_app()
    app.settings["application"] = app
    app.listen(BIND_PORT, BIND_IP)
    tornado.ioloop.IOLoop.current().start()