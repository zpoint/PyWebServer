import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from app.Stock.DataBase import DBUtil
from app.Stock.StockLogin import StockLogin
from ConfigureUtil import Headers, WebPageBase, ErrorReturn


class StockBind(View):
    path = "/Stock/StockBind"
    async def get(self):
        if not DBUtil.valid_user(self.request.headers["Cookie"]):
            return ErrorReturn.invalid()

        html = WebPageBase.head("请绑定账号")
        html += """
        <form action="%s" method="post">
        <table border=0 align="center">
        <tr>
        <td>对方平台用户名</td>
        <td><input type="text" name="username" pattern="^[\da-zA-Z]{1,}$" title="请输入需要进行自动操作的用户名" /></td>
        </tr>
        <tr>
        <td>对应账户密码</td>
        <td><input type="password" name="password" pattern="^[\da-zA-Z]{1,}$" title="请输入对应账户的密码" /></td>
        </tr>
        <tr>
        <td>picture</td>
        <td><input type="text" name="verifyCode" pattern="^[\da-zA-Z]{1,}$" title="请输入图片显示的验证码" /></td>
        </table>
        <table border=0 align="center">
        <td><input type="submit" align="center" value="绑定" /></td>
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

        keys = ("verify_code", "verify_value", "username", "password", "cid", "cname")
        for key in keys:
            if key not in post_body:
                return ErrorReturn.invalid()

        success, msg = StockLogin.login(post_body["verify_code"], post_body["verify_value"], post_body["username"],
                                        post_body["password"], post_body["cid"], post_body["cname"])
        if not success:
            return ErrorReturn.html(msg, self.path)
        else:
            DBUtil.bind(self.request.headers["Cookie"], post_body)
