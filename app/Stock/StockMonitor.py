from aiohttp import web
from aiohttp.web import View

from app.Stock.DataBase import DBUtil
from app.Stock.StockLogin import StockLogin, login
from ConfigureUtil import Headers, WebPageBase, ErrorReturn


class StockMonitor(View):
    path = "/Stock/StockMonitor"

    @staticmethod
    def personal_head(r):
        return """
        <table border=1 align="center">
        <tr><td>用户名</td><td>绑定账号</td><td>线路</td><td>过期时间</td><td>邀请码</td></tr>
        <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>
        </table>
        """ % (r["username"], r["bind_username"], "线路", r["expired"].strftime("%Y-%m-%d"), r["inviting_code"].upper())

    async def get(self):
        r = DBUtil.valid_user(self.request.cookies, True)
        if not r:
            return ErrorReturn.invalid()
        if not r["bind_username"]:
            return ErrorReturn.invalid("您尚未绑定账号,请绑定后进行操作", main_path="/Stock/StockBind")

        html = WebPageBase.head("监控系统")
        html += self.personal_head(r)
        html += "</body></html>"
        return web.Response(text=html, headers=Headers.html_headers)
