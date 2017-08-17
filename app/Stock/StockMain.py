import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from ConfigureUtil import global_session, Headers, ErrorReturn
from app.Stock import Config
from app.Stock.DataBase import DBUtil

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


class StockSystemLogin(View):
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
        <form action="%s" method="post">
        <table border=0 align="center">
        <tr>
        <td>用户名</td>
        <td><input type="text" name="username" pattern="^[\da-zA-Z]{3,10}$" title="请输入注册时的用户名, 必须3-10位的字母数字" /></td>
        <td>密码</td>
        <td><input type="password" name="password" pattern="^[\da-zA-Z]{6,18}$" title="请输入注册时的密码, 必须6-18位的字母数字" /></td>
        </tr></table>
        <table border=0 align="center">
        <tr align="center"><td><a href="Stock/StockRegister">新用户?点我注册</a></tr>
        <tr align="center"><td><input type="submit" align="center" value="登陆" /></td></tr>
        </table>
        </form>
    </html>
    """ % (self.path, ), headers=Headers.html_headers)

    async def post(self):
        text = await self.request.text()
        values = text.split("&")
        post_body = dict()
        for v in values:
            inner_values = v.split("=")
            if len(inner_values) != 2:
                return ErrorReturn.html("非法访问", self.path)
            post_body[inner_values[0]] = inner_values[1]

        if "username" not in post_body or "password" not in post_body:
            return ErrorReturn.html("非法访问", self.path)

        valid, cookie = DBUtil.get_and_reset_cookie(post_body["username"], post_body["password"])
        if not valid:
            return ErrorReturn.html(cookie, self.path)

        init_headers = Headers.html_headers
        init_headers["Set-Cookie"] = "UID=" + cookie
        return ErrorReturn.html("登陆成功, 即将跳转进入", "/Stock/StockLogin", "登陆成功", headers=init_headers)\
