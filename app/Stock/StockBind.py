import base64
from aiohttp import web
from aiohttp.web import View
from urllib.parse import quote

from app.Stock.DataBase import DBUtil
from app.Stock.StockLogin import StockLogin, login
from ConfigureUtil import Headers, WebPageBase, ErrorReturn


class StockBind(View):
    path = "/Stock/StockBind"
    async def get(self):
        r = DBUtil.valid_user(self.request.cookies, True)
        if not r:
            return ErrorReturn.invalid()

        img_byte = await StockLogin.get_img_byte(r)

        html = WebPageBase.head("请绑定账号")
        html += """
        <h3 align='center'>您还未绑定账号，请绑定后进行使用</h2>
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
        <td><img src="data:image/png;base64, %s"></td>
        <td><input type="text" name="verify_code" pattern="^[\da-zA-Z]{1,}$" title="请输入图片显示的验证码" /></td>
        </table>
        <table border=0 align="center">
        <tr><td><a href="%s">刷新验证码</a></td></tr>
        <tr><td><input type="submit" align="center" value="绑定" /></td>
        </tr></table>
        </form>
        </body>
        </html>
        """ % (self.path, quote(base64.encodebytes(img_byte)), self.path)
        return web.Response(text=html, headers=Headers.html_headers)

    async def post(self):
        r = DBUtil.valid_user(self.request.cookies, True)
        if r is False:
            return ErrorReturn.invalid()

        text = await self.request.text()
        values = text.split("&")
        post_body = dict()
        for v in values:
            inner_values = v.split("=")
            if len(inner_values) != 2:
                return ErrorReturn.invalid()
            post_body[inner_values[0]] = inner_values[1]

        post_body.update(r["bind_param"])
        keys = ("verify_code", "verify_value", "username", "password", "cid", "cname")
        for key in keys:
            if key not in post_body:
                return ErrorReturn.invalid(title="参数不合法", main_path=self.path)

        success, cookie_dict = await login(r["prefer_host"], post_body["verify_code"], post_body["verify_value"],
                                           post_body["username"], post_body["password"], post_body["cid"],
                                           post_body["cname"], r["bind_cookie"])

        if not success:
            return ErrorReturn.html(cookie_dict, self.path)
        else:
            DBUtil.update_param(r, {}, cookie_dict, False)
            DBUtil.bind(r, post_body)
