import hashlib
import logging
import json
from urllib.parse import unquote
from app.Stock.Config import config
from ConfigureUtil import Headers, global_session, global_loop, ErrorReturn

verify_code_url = "http://api.ruokuai.com/create.json"
verify_code_param = """---------------RK\r
Content-Disposition: form-data; name="username"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="password"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="typeid"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="timeout"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="softid"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="softkey"\r
\r
%s\r
---------------RK\r
Content-Disposition: form-data; name="image"; filename="1.png"\r
Content-Type: application/octet-stream\r
Content-Transfer-Encoding: base64\r
\r
%s\r
---------------RK--"""

verify_code_headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-cn",
    "Content-Type": "multipart/form-data; boundary=-------------RK",
    "Host": "api.ruokuai.com"
}


class VerifyUtilObject(object):
    def __init__(self, session=None):
        self.session = global_session if not session else session

    async def get_verify_value_from_ruokuai(self, img_b64):
        data = verify_code_param % (config["ruokuai"]["username"], config["ruokuai"]["password"],
                                    config["ruokuai"]["typeid"], config["ruokuai"]["timeout"],
                                    config["ruokuai"]["softid"], config["ruokuai"]["softkey"], unquote(img_b64))

        async with self.session.post(verify_code_url, data=data.encode("utf8"), headers=verify_code_headers) as resp:
            text = await resp.text()
            json_obj = json.loads(text)
            if "Error" in json_obj:
                logging.error(json_obj["Error"])
                return False, None
            else:
                return True, json_obj["Result"]

    async def get_verify_value_from_model(self, img_b64):
        pass

    async def get_verify_value(self, img_b64):
        if config["ruokuai"]["use_model"] == "1":
            return await self.get_verify_value_from_model(img_b64)
        else:
            return await self.get_verify_value_from_ruokuai(img_b64)

    @staticmethod
    def save_img(img_byte, value):
        path = config["common"]["img_save_path"] + str(value) + "_" + hashlib.md5(img_byte).hexdigest()
        with open(path, "wb") as f:
            f.write(img_byte)


verifyUtil = VerifyUtilObject()
