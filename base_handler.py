# coding: utf-8
import json

from tornado.web import RequestHandler


class BaseRequestHandler(RequestHandler):

    def __init__(self, *args, **kwargs):
        super(BaseRequestHandler, self).__init__(*args, **kwargs)

    def write_response(self, data=None, status=1, err_msg=None):
        """
        快速返回json格式数据
        mod: whb
        """
        self.set_header('Content-type', 'application/json')
        _data = {
            "status": int(status)
        }
        if data is not None:
            _data.update(data)
        if not status:
            if err_msg is not None:
                _data["err_msg"] = err_msg
        self.write(json.dumps(_data))

    def get_current_user(self):
        return True