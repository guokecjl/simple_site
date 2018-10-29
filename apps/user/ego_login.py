# coding: utf-8

import json

from tornado.gen import coroutine
from redis import StrictRedis
from uuid import uuid1

from base_handler import BaseRequestHandler
from utils.ego import EgoLib
from config import EID, PRIVATE_KEY, SCENE_ID, EXPIRES_IN, PUBLIC_KEY


class GetLoginResultHandler(BaseRequestHandler):
    @coroutine
    def get(self):
        try:
            gid = self.get_argument('gid', None)
            scene_id = self.get_argument('scene_id', None)
            if not (gid and scene_id):
                self.write_response(status=0, err_msg='缺少必要的参数')
                return
            client = StrictRedis()
            write_data = client.get(scene_id + gid)
            if not write_data:
                self.write_response(status=0, err_msg='尚未收到验证信息')
                return
            self.write_response(json.loads(write_data))
        except:
            import traceback
            traceback.print_exc()


class ReceiveUserInfoHandler(BaseRequestHandler):
    @coroutine
    def post(self):
        try:
            sign = self.get_argument('sign', None)
            gid = self.get_argument('gid', None)
            scene_id = self.get_argument('to_scene_id', None)
            if sign and gid and scene_id:
                client = StrictRedis()
                client.set(scene_id+gid, json.dumps({
                    'login_status': 'login'
                }), 180)
                self.write_response()
        except:
            self.write_response(status=0, err_msg='数据库异常')


class GetQrCodeHandler(BaseRequestHandler):
    @coroutine
    def get(self):
        eg = EgoLib(EID, PRIVATE_KEY, EXPIRES_IN)
        gid = uuid1().hex
        client = StrictRedis()
        client.set(gid, True, EXPIRES_IN)
        url = eg.create_qr_code_url_str(SCENE_ID, gid)

        # todo: delete
        data = {
            "templates": {
                'zhouxi': 1234
            },
            "gid": gid,
            "to_eid": EID,
            "to_scene_id": SCENE_ID,
        }
        try:
            eg.decode_verified_identity(data, b'Gm4TrMQT8k+MzwdsGYAgS8sH2rwihxca5fYuO/JrMKCCrnmqCYN3CfTcmIgq09rygWKg8hutApfWaOUefzpQVg==', PUBLIC_KEY)
        except:
            pass

        self.write_response({'url': url})


class UserScanHandler(BaseRequestHandler):
    @coroutine
    def post(self):
        try:
            gid = self.get_argument('gid', None)
            scene_id = self.get_argument('to_scene_id', None)
            if gid and scene_id:
                client = StrictRedis()
                client.set(scene_id+gid, json.dumps({'login_status': 'scan'}), 180)
                self.write_response()
                return
        except:
            self.write_response(status=0, err_msg='数据库异常')
            return