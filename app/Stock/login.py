import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from ConfigureUtil import global_session, Headers
from app.Stock import Config

basic_headers = {
    "Host": str(Config.Host),
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "close"
}

async def get_code_info():
    url = Config.Host + "/getCodeInfo/.auth?" + urlencode({
        "u": str(random.random()),
        "systemversion": Config.systemVersion,
        ".auth": ""
    })
    async with global_session.get(url, basic_headers=basic_headers) as resp:
        text = await resp.text()
        c_user, verify_value, _ = text.split("_")
    return c_user, verify_value

async def get_verify_code(c_user):
    url = Config.Host + "/getVcode/.auth?" + urlencode({
        "t": c_user,
        "systemversion": Config.systemVersion,
        ".auth": ""
    })
    async with global_session.get(url, headers=basic_headers) as resp:
        byte_img = await resp.read()
        return byte_img

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


class StockLogin(View):
    path = "/Stock"

    async def get(self):
        return web.Response(text="""
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html>
    <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    </head>
    <title>自动系统登录窗口</title>
    <h1 align="center">自动系统登陆窗口</h1>
    <p align="center">请登录自动系统</p>
        <form action="/Stock/login" method="post">
        <table border=0 align="center">
        <tr>
        <td>用户名</td>
        <td><input type="text" name="username" pattern="^[\da-zA-Z]{3,10}$" title="请输入注册时的用户名" /></td>
        <td>密码</td>
        <td><input type="password" name="password" pattern="^[\da-zA-Z]{6,18}$" title="请输入注册时的密码" /></td>
        </tr></table>
        <table border=0 align="center">
        <td><input type="submit" align="center" value="登陆" /></td>
        </tr></table>
        </form>
    </html>
    """, headers=Headers.html_headers)
