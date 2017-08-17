import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from app.Stock.DataBase import DBUtil
from app.Stock.StockLogin import StockLogin
from ConfigureUtil import Headers, WebPageBase, ErrorReturn


class StockBind(View):
    path = "/Stock/StockRegister"
    async def get(self):
        if not DBUtil.valid_user(self.request.headers["Cookie"]):
            return ErrorReturn.invalid()

        html = WebPageBase.head("请注册账号")
        html += """
        <form action="%s" method="post">
        <table border=0 align="center">
        <tr>
        <td>用户名</td>
        <td><input type="text" name="username" pattern="^[\da-zA-Z]{3,10}$" title="3-10位的字母数字" /></td>
        </tr>
        <tr>
        <td>密码</td>
        <td><input type="password" name="password" pattern="^[\da-zA-Z]{6,18}$" title="6-18位的字母数字" /></td>
        </tr>
        <tr>
        <td>邀请码</td>
        <td><input type="text" name="inviteCode" pattern="^[\da-zA-Z]{1,}$" title="请输入邀请码" /></td>
        </table>
        <table border=0 align="center">
        <td><input type="submit" align="center" value="注册" /></td>
        </tr></table>
        </form>
        </body>
        </html>
        """ % (self.path, )
        return web.Response(text=html, headers=Headers.html_headers)

    async def post(self):
        if not DBUtil.valid_user(self.request.headers["Cookie"]):
            return ErrorReturn.invalid()

        text = await self.request.text()
        values = text.split("&")
        post_body = dict()
        for v in values:
            inner_values = v.split("=")
            if len(inner_values) != 2:
                return ErrorReturn.invalid()
            post_body[inner_values[0]] = inner_values[1]

        keys = ("username", "password", "inviteCode")
        for key in keys:
            if key not in post_body:
                return ErrorReturn.invalid()

        success, msg = DBUtil.create_user(post_body["username"], post_body["password"], post_body["inviteCode"])
        if not success:
            return ErrorReturn.html(msg, self.path)
        else:
            return ErrorReturn.html(msg, StockLogin.path)