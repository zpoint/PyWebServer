import re
import asyncio
import random
import lxml.html
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode
from collections import OrderedDict

from app.Stock.DataBase import DBUtil
from app.Stock.Config import config
from app.Stock.FunctionUtil import generate_cookie, get_cookie_dict, generate_headers
from ConfigureUtil import Headers, global_session, global_loop, ErrorReturn


async def get_cid_and_cname(host, session=None):
    session = global_session if not session else session
    url = host + "/sczzz365482f/user/login.html.auth"
    basic_headers = generate_headers(connection="keep-alive")
    basic_headers["Host"] = host.replace("http://", "")
    async with session.get(url, headers=basic_headers) as resp:
        text = await resp.text()
        page = lxml.html.fromstring(text)
        cid_input = page.xpath('.//input[@type="hidden" and @name="cid"]')[0]
        cname_input = page.xpath('.//input[@type="hidden" and @name="cname"]')[0]
    return cid_input.attrib["value"], cname_input.attrib["value"]


async def get_code_info(host, sys_version, session=None):
    session = global_session if not session else session
    url = host + "/getCodeInfo/.auth?" + urlencode({
        "u": str(random.random()),
        "systemversion": sys_version,
        ".auth": ""
    })
    basic_headers = generate_headers(connection="keep-alive")
    basic_headers["Host"] = host.replace("http://", "")
    async with session.get(url, headers=basic_headers) as resp:
        text = await resp.text()
        c_user, verify_value, _ = text.split("_")
    return c_user, verify_value, get_cookie_dict(resp.cookies)


async def get_verify_code(host, c_user, cookie_dict, session=None):
    session = global_session if not session else session
    url = host + "/getVcode/.auth?" + urlencode({
        "t": c_user,
        "systemversion": config["remote"]["systemversion"],
        ".auth": ""
    })
    basic_headers = generate_headers(connection="keep-alive")
    basic_headers["Host"] = host.replace("http://", "")
    basic_headers["Cookie"] = generate_cookie(cookie_dict)
    async with session.get(url, headers=basic_headers) as resp:
        byte_img = await resp.read()
        return byte_img, get_cookie_dict(resp.cookies)


async def login(host, verify_code, verify_value, username, password, cid, cname, cookie_dict, session=None):
    session = global_session if not session else session
    url = host + "/loginVerify/.auth"
    param = OrderedDict([
        ("VerifyCode", verify_code),
        ("__VerifyValue", verify_value),
        ("__name", username),
        ("password", password),
        ("isSec", "0"),
        ("cid", cid),
        ("cname", cname),
        ("systemversion", config["remote"]["systemversion"]),
    ])
    basic_headers = generate_headers()
    basic_headers["Referer"] = host + "/sczzz365482f/user/login.html.auth"
    basic_headers["Host"] = host.replace("http://", "")
    basic_headers["Cookie"] = generate_cookie(cookie_dict)
    basic_headers["Origin"] = "http://pc12.x.sss33.us"
    basic_headers["Content-Type"] = "application/x-www-form-urlencoded;"
    async with session.post(url, data=urlencode(param), headers=basic_headers) as resp:
        html = await resp.text()

        if "AC" not in resp.cookies:
            return False, html if "Server Error" not in html else "对方服务器异常, 请稍后重试"

        real_login_host = re.search("http://.+", html)
        if not real_login_host:
            return False, "内部匹配错误"

        cookie_dict_a = get_cookie_dict(resp.cookies)
        cookie_dict.update(cookie_dict_a)
        basic_headers["Cookie"] = generate_cookie(cookie_dict)
        basic_headers["Connection"] = "keep-alive"

        real_login_host = real_login_host.group(0).strip().replace("host", host.replace("http://", ""))
        async with session.get(real_login_host, headers=basic_headers) as resp2:
            text = await resp2.text()
            cookie_dict_b = get_cookie_dict(resp2.cookies)
            cookie_dict_b.update(cookie_dict_a)

        return True, cookie_dict_b


class StockLogin(View):
    path = "/Stock/StockLogin"

    async def get(self):
        bind_usr = DBUtil.valid_user(self.request.cookies, "bind_username")
        if bind_usr is False:
            return ErrorReturn.invalid()
        elif bind_usr is None:
            return web.Response(text="""<head><meta http-equiv="refresh" content="0;url=%s"></head>""" %
                                     ("/Stock/StockBind", ),
                                headers=Headers.html_headers)
        else:
            return web.Response(text="""<head><meta http-equiv="refresh" content="0;url=%s"></head>""" %
                                     ("/Stock/StockMonitor", ),
                                headers=Headers.html_headers)

    @staticmethod
    async def get_img_byte(r, old_user=False, loop=None, session=None):
        loop = global_loop if not loop else loop
        if old_user:
            r["bind_cookie"] = None
            r["bind_param"] = None
        values_a, values_b = await asyncio.gather(get_cid_and_cname(r["prefer_host"], session),
                                                  get_code_info(r["prefer_host"], config["remote"]["systemversion"],
                                                                session),
                                                  loop=loop)
        cid, cname = values_a
        c_user, verify_value, cookie_dict = values_b
        param_dict = {
            "cid": cid,
            "cname": cname,
            "c_user": c_user,
            "verify_value": verify_value
        }
        DBUtil.update_param(r, param_dict, cookie_dict, commit=False)

        byte_img, cookie_dict_img = await get_verify_code(r["prefer_host"], r["bind_param"]["c_user"],
                                                          r["bind_cookie"], session)
        DBUtil.update_param(r, {}, cookie_dict_img)
        return byte_img
