from aiohttp import web
from aiohttp.web import View

from ConfigureUtil import Headers, ErrorReturn
from app.Stock.Config import config
from app.Stock.DataBase import DBUtil
from app.Stock.StockRegister import StockBind
from app.Stock.StockLogin import StockLogin


class StockSystemLogin(View):
    path = "/Stock"

    async def get(self):
        if DBUtil.valid_user(self.request.cookies):
            return web.Response(text="""<head><meta http-equiv="refresh" content="0;url=%s"></head>""" %
                                     (StockLogin.path, ),
                                headers=Headers.html_headers)

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
        <tr align="center"><td><a href="%s">新用户?点我注册</a></td></tr>
        <tr align="center"><td><input type="submit" align="center" value="登陆" /></td></tr>
        </table>
        </form>
    </html>
    """ % (self.path, StockBind.path), headers=Headers.html_headers)

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

        extra_info = self.request.transport.get_extra_info('peername')
        ip = extra_info[0] if extra_info is not None else str(None)

        valid, cookie = DBUtil.get_and_reset_cookie(post_body["username"], post_body["password"], ip)
        if not valid:
            return ErrorReturn.html(cookie, self.path)

        init_headers = Headers.html_headers
        init_headers["Set-Cookie"] = "StockID=" + cookie + ";path=/;max-age=" + config["common"]["cookie_max_age"]
        return ErrorReturn.html("登陆成功, 即将跳转进入", "/Stock/StockLogin", "登陆成功", headers=init_headers)\
