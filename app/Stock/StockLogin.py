import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from app.Stock import Config
from app.Stock.DataBase import DBUtil
from ConfigureUtil import Headers, global_session


basic_headers = {
    "Host": str(Config.Host),
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "close"
}


class StockLogin(View):
    path = "/Stock/StockLogin"
    async def get(self):
        if not DBUtil.isbind(self.request.headers["Cookie"]):
            return web.Response(text="""<head><meta http-equiv="refresh" content="0;url=/Stock/StockBind"></head>""",
                                headers=Headers.html_headers)

    @staticmethod
    async def login(verify_code, verify_value, username, password, cid, cname):
        url = Config.Host + "/loginVerify/.auth?"
        param = {
            "VerifyCode": verify_code,
            "__VerifyValue": verify_value,
            "__name": username,
            "password": password,
            "isSec": "0",
            "cid": cid,
            "cname": cname,
            "systemversion": Config.systemVersion,
        }
        url += urlencode(param)
        async with global_session.get(url, basic_headers=basic_headers) as resp:
            print(resp.cookies, repr(resp.cookies), type(resp.cookies))
