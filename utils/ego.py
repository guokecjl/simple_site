# coding: utf-8

import sys
PY3 = sys.version_info >= (3, 0)

if PY3:
    from urllib.parse import urlencode
else:
    from urllib import urlencode

import base64
import json
from copy import deepcopy
import time

import rsa
import jwt

VERSION = "1.0.0"


class EgoLib(object):

    API_DOMAIN = "192.168.1.254:8888"
    API_URL_PREFIX = "http"
    AUTH_QR_CODE_HANDLER = "/auth/verify_qr_code"
    GET_IDENTITY_FORWARDLY_HANDLER = "/identity"
    CHARSET = "utf-8"
    RSA_BLOCK_LENGTH = 128

    def __init__(
            self,
            eid,  # str
            private_key,  # str or bytes(PY3)
            qr_code_expires=180  # int
    ):
        self.eid = eid
        self.private_key = private_key
        self.QR_CODE_EXPIRES = int(qr_code_expires)
        self.PRIVATE_KEY = self._load_private_key(private_key)

    def create_qr_code_url_str(
            self,
            scene_id,  # str
            gid  # str
    ):
        """
        创建二维码展示的url
        """
        data = {
            "eid": self.eid,
            "expire_at": int(time.time()) + self.QR_CODE_EXPIRES,
            "scene_id": scene_id,
            "gid": gid,
            "key_id": '5bcd76c524c7651c5053ee38-key1'
        }
        signed_data = self._get_signed_content(data)
        return "{}://{}{}?{}".format(self.API_URL_PREFIX, self.API_DOMAIN,
                                     self.AUTH_QR_CODE_HANDLER, signed_data)

    def decode_verified_identity(
            self,
            data,  # dict， 回调接口（或者是主动查询接口）收到的所有参数组成的字典
            owner_signature,  # str or bytes(PY3)，信息授权方的签名
            owner_public_keyfile,  # str，信息授权放的公钥字符串，标准PEM格式或者
                                   # PEM格式字符串去掉头尾和换行的字符串都均可
            verify_exp=True,  # bool，是否校验过期时间（声明设置了过期时间exp）
            verify_nbf=True,  # bool，是否校验生效时间（声明设置了生效时间nbf）
            verify_iat=True,  # bool，是否校验签发时间（声明设置了签发时间iat）
    ):
        """
        解析并验证客户发过来的认证信息，未通过认证的声明将不会返回
        note：此时获取到的身份信息还不是完全可信，
        还要在链上检查声明的状态，确认声明已经上链并且没有被吊销
        """
        # 验证授权方的签名
        if PY3 and isinstance(owner_signature, str):
            owner_signature = owner_signature.encode(self.CHARSET)
        owner_public_key = self._load_public_key(owner_public_keyfile)
        if not self._verify_owner_signature(data, owner_signature,
                                            owner_public_key):
            return

        # 使用私钥对身份信息进行解密
        templates = self._decrypt_templates(data["templates"])
        if not isinstance(templates, dict):
            return

        # 解析并校验声明的签名信息
        identity_info = {}
        for tempate_name, claim in templates.items():
            verified_claim = self._decode_verified_claim(claim, verify_exp,
                                                         verify_nbf, verify_iat)
            if not verified_claim:
                continue
            header, payload = verified_claim
            identity_info[tempate_name] = {
                "header": header,
                "payload": payload
            }
        return identity_info

    def get_claim_status(
            self,
            kyc_ids  # tuple or list
    ):
        """
        去链上获取kyc声明的状态
        每个声明有3种状态：None（声明未上链）、normal（正常声明）、revoked（声明被吊销）
        """
        # todo：测试暂时先认为都是正常的
        return {kyc_id: "normal" for kyc_id in kyc_ids}

    def get_identity_forwardly_url(
            self,
            scene_id,  # str
            gid  # str
    ):
        """
        主动调用接口查询某授权方授权的身份信息，由于网络等原因，发送到回调接口的信息有可能
        无法收到，所以需要主动获取身份信息的方法来补充
        """
        sign_data = {
            "eid": self.eid,
            "scene_id": scene_id,
            "gid": gid
        }
        signed_content = self._get_signed_content(sign_data)
        return "{}://{}{}?{}".format(
            self.API_URL_PREFIX, self.API_DOMAIN,
            self.GET_IDENTITY_FORWARDLY_HANDLER, signed_content
        )

    @staticmethod
    def _load_private_key(
            keyfile  # str or bytes(PY3)
    ):
        """
        载入私钥文件
        """
        if PY3 and isinstance(keyfile, bytes):
            keyfile = keyfile.decode("utf-8")
        keyfile = keyfile.strip()
        if not keyfile.startswith("-----BEGIN RSA PRIVATE KEY-----"):
            keyfile = "-----BEGIN RSA PRIVATE KEY-----\n" + \
                      keyfile
        if not keyfile.endswith("-----END RSA PRIVATE KEY-----"):
            keyfile += "\n-----END RSA PRIVATE KEY-----"
        if PY3:
            keyfile = keyfile.encode("utf-8")
        return rsa.PrivateKey.load_pkcs1(keyfile)

    @staticmethod
    def _load_public_key(
            keyfile  # str or bytes(PY3)
    ):
        """
        载入公钥文件
        """
        if PY3 and isinstance(keyfile, bytes):
            keyfile = keyfile.decode("utf-8")
        keyfile = keyfile.strip()
        if not keyfile.startswith("-----BEGIN RSA PUBLIC KEY-----"):
            keyfile = "-----BEGIN RSA PUBLIC KEY-----\n" + \
                      keyfile
        if not keyfile.endswith("-----END RSA PUBLIC KEY-----"):
            keyfile += "\n-----END RSA PUBLIC KEY-----"
        if PY3:
            keyfile = keyfile.encode("utf-8")
        return rsa.PublicKey.load_pkcs1(keyfile)

    @staticmethod
    def _get_cert_provider_public_key(
            issuer_id,  # str，签名者id
            algorithm  # str，签名算法
    ):
        """
        根据声明的签名id和签名算法获取公钥信息
        """
        if issuer_id != "977591a4ede04343bdd51b2c2f8da6fb":
            return
        pub_k = \
            '-----BEGIN RSA PUBLIC KEY-----\n' \
            'MIGJAoGBAKFIesGKTtCVEGLANw15ytCnIAFEFBCeP+w+mNT6f8BcIQT6uEuO/2/u\n' \
            'x+THJXqSjM5gKVUOFW2oCDKpiqQvj0Myg2hCBZ37kQ5bkDvDEG1huyp2w4HdCXMI\n' \
            'czts+/+fBTgOnVvhPPhENOu7LBjL9e1SHZR6w9pQCsMv7igSrjy3AgMBAAE=\n' \
            '-----END RSA PUBLIC KEY-----\n'
        return pub_k

    @staticmethod
    def _sort_params(
            params  # dict
    ):
        """
        对参数排序
        """
        return sorted(params.items())

    def _get_sign_content(self, params):
        """
        生成需要签名的字符串
        :param params:
        """
        sign_content = []
        for k, v in self._sort_params(params):
            value = v if isinstance(v, str) else json.dumps(v)
            sign_content.append("{}={}".format(k, value))
        return "&".join(sign_content)

    def _sign(self, params, private_key):
        """

        :param params:
        :param private_key:
        :return:
        """
        sign_content = self._get_sign_content(params)
        if PY3:
            sign_content = sign_content.encode("utf-8")
        signature = rsa.sign(sign_content, private_key, 'SHA-256')
        sign = base64.b64encode(signature)
        if PY3:
            sign = sign.decode(self.CHARSET)
        return sign

    def _get_signed_content(
            self,
            params  # dict，请求的所有参数组成的字典
    ):
        """
        对请求参数签名，将签名值加入请求参数并urlencode后的字符串
        """
        sign = self._sign(params, self.PRIVATE_KEY)
        signed_params = deepcopy(params)
        signed_params["sign"] = sign
        return urlencode(signed_params)

    def _decrypt_templates(
            self,
            encrypted_templates  # str，加密的templates信息
    ):
        """
        解密授权方利用服务方公钥进行加密后的templates信息
        """
        try:
            encrypted_templates = base64.b64decode(
                encrypted_templates.encode("utf-8"))
            encrypted_length = len(encrypted_templates)
            message = b''
            i = 0
            while i + self.RSA_BLOCK_LENGTH <= encrypted_length:
                message += rsa.decrypt(
                    encrypted_templates[i: i + self.RSA_BLOCK_LENGTH],
                    self.PRIVATE_KEY)
                i += self.RSA_BLOCK_LENGTH
            message = base64.b64decode(message).decode("utf-8")
            return json.loads(message)
        except BaseException:
            return

    def _verify_owner_signature(
            self,
            data,  # dict，回调接口（或者是主动查询接口）收到的所有参数组成的字典
            signature,  # bytes(PY3)
            public_key  # rsa.PublicKey
    ):
        """
        校验授权方的签名
        """
        if not ("templates" in data and "gid" in data and "to_eid" in data and
                "to_scene_id" in data):
            return
        owner_sign_data = {
            "templates": data["templates"],
            "gid": data["gid"],
            "to_eid": data["to_eid"],
            "to_scene_id": data["to_scene_id"],
        }
        owner_sign_content = self._get_sign_content(
            owner_sign_data).encode("utf-8")
        from config import PRIVATE_KEY
        signature = base64.b64decode(signature)
        owner_sign_data.update({
            'sign': (base64.b64encode(rsa.sign(owner_sign_content, rsa.PrivateKey.load_pkcs1(PRIVATE_KEY), 'SHA-256'))).decode('utf-8'),
            'key_id': '5bc6dd445f627d66bab97e82-key1'
        })
        print(urlencode(owner_sign_data))
        return rsa.verify(owner_sign_content, signature, public_key)

    def _decode_verified_claim(
            self,
            claim,  # str
            verify_exp=True,  # bool
            verify_nbf=True,  # bool
            verify_iat=True,  # bool
    ):
        try:
            header = jwt.get_unverified_header(claim)
            algorithm = header.get("alg")
            if not algorithm:
                return
            payload = jwt.decode(claim, verify=False)
            issuer_id = payload.get("iss")
            pub_k = self._get_cert_provider_public_key(issuer_id, algorithm)
            if not pub_k:
                return
            return header, jwt.decode(claim, pub_k, options={
                'verify_signature': True,
                'verify_exp': verify_exp,
                'verify_nbf': verify_nbf,
                'verify_iat': verify_iat
            })
        except BaseException:
            return
