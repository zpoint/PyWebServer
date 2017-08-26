import copy
import base64
import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import quote
from datetime import datetime

from app.Stock.Rules import rule
from app.Stock.DataBase import DBUtil
from app.Stock.Config import stock_pool
from app.Stock.StockLogin import StockLogin, login
from app.Stock.RefreshManger import next_refresh_data
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

    async def re_login(self, r, post_body):
        post_body.update(r["bind_param"])
        post_body["username"] = r["bind_username"]
        post_body["password"] = r["bind_password"]
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
            DBUtil.set_cookie_valid(r)
            html = await self.get_content_html(r)
            return web.Response(text=html, headers=Headers.html_headers)

    async def get_content_html(self, r):
        html = WebPageBase.head("监控系统")
        html += self.personal_head(r)
        html += """
            <form action="" method="post"> 
            """
        html += await self.get_middle_content(r)
        html += "</form>"
        if next_refresh_data:
            now = datetime.now()
            next_seconds = (next_refresh_data - now).second + random.randint(15, 30)
        else:
            next_seconds = 5 * 60

        html += """
            <span id="time">%d</span> 秒后自动刷新</a></p>
            <script type="text/javascript">  
            delayURL();    
            function delayURL() { 
            var delay = document.getElementById("time").innerHTML;
                    var t = setTimeout("delayURL()", 1000);
                if (delay > 0) {
                    delay--;
                    document.getElementById("time").innerHTML = delay;
                } else {
                    clearTimeout(t); 
                    window.location.href = "%s";
                }        
                } 
                </script>
        """ % (next_seconds, self.path)
        html += "</body></html>"
        return html

    async def get(self):
        r = DBUtil.valid_user(self.request.cookies, True)
        if not r:
            return ErrorReturn.invalid()
        if not r["bind_username"]:
            return ErrorReturn.invalid("您尚未绑定账号,请绑定后进行操作", main_path="/Stock/StockBind")

        html = await self.get_content_html(r)
        return web.Response(text=html, headers=Headers.html_headers)

    async def post(self):
        r = DBUtil.valid_user(self.request.cookies, True)
        if not r:
            return ErrorReturn.invalid()
        if not r["bind_username"]:
            return ErrorReturn.invalid("您尚未绑定账号,请绑定后进行操作", main_path="/Stock/StockBind")

        text = await self.request.text()
        values = text.split("&")
        post_body = dict()
        for v in values:
            inner_values = v.split("=")
            if inner_values[0] == "rule":
                if "rule" in post_body:
                    post_body["rule"].append(inner_values[1])
                else:
                    post_body["rule"] = [inner_values[1]]

            post_body[inner_values[0]] = inner_values[1]

        if "verify_code" in post_body:
            return await self.re_login(r, post_body)
        else:
            for key in ("base_value", "stock_times", "working_period"):
                if key not in post_body:
                    return ErrorReturn.invalid("非法访问", main_path=self.path)

            success, reason = self.update_personal_val(post_body, r)
            if not success:
                return ErrorReturn.invalid(reason, main_path=self.path)

            html = await self.get_content_html(r)
            return web.Response(text=html, headers=Headers.html_headers)

    @staticmethod
    def update_personal_val(post_body, r):
        if "rule" in post_body:
            new_rule_val = rule.get_rule_val(post_body["rule"])
        else:
            new_rule_val = r["rules"]
        try:
            new_base_val = float(post_body["base_value"])
        except ValueError:
            return False, "请输入整数或者小数基数"

        values = post_body["stock_times"].split("-")
        if len(values) < 2:
            return False, "倍数输入有误"
        for i in values:
            if not i.isdigit():
                return False, "输入的倍数必须为整数"

        new_stock_val = post_body["stock_times"]

        new_period = post_body["working_period"]
        values = new_period.split("-")
        if len(values) != 2:
            return False, "进行自动购买的时段需同 00-24 格式一致"
        left, right = values
        if not left.isdigit() or not right.isdigit():
            return False, "进行自动购买的时段需同 00-24 格式一致, 两边均为整数"
        if int(left) > 24 or int(left) < 0 or int(right) > 24 or int(right) < 0:
            return False, "进行自动购买的时段需同 00-24 格式一致, 时段需在24小时范围内"
        DBUtil.update_base(r, new_rule_val, new_base_val, new_stock_val, new_period)

    async def get_middle_content(self, r):
        if not DBUtil.check_cookie_valid(r):
            img_byte = await StockLogin.get_img_byte(r)
            body = "<h2 align=\"center\">您已在其他地方登录,　或已掉线, 请重新输入验证码进行登录</h2>"
            body += """<table align="center">  
            <tr>      
            <td><img src="data:image/png;base64, %s"></td>
            <td><input type="text" name="verify_code" pattern="^[\da-zA-Z]{1,}$" title="请输入图片显示的验证码" /></td>
            </tr>
            </table>
            <table border=0 align="center">
            <tr><td><a href="%s">刷新验证码</a></td></tr>
            <tr><td><input type="submit" align="center" value="提交" /></td></tr>
            </table>""" % (quote(base64.encodebytes(img_byte)), self.path)
            return body
        else:
            rule_table, row_count = self.get_rule_table(r)
            return """
            <table align="center">
            <tr><td>%s</td>
                <td>%s</td>
            </tr>
            <tr><td><input type="submit" align="center" value="提交" /></td></tr>
            </table>
            """ % (rule_table, self.get_stock_info_table(r, row_count))

    def get_rule_table(self, r):
        row_count = 0
        body = "<table border=1>"
        body += "<caption><h3>我的规则</h3></caption>"
        for rule_name, values in rule.all_rules.items():
            _, desc, color = values
            body += '<tr><td><label><input name="rule" type="checkbox" value="%s" %s /></label></td><td ' \
                    'bgcolor="%s">%s</td></tr>' % \
                    ('checked="checked' if rule.has_rule(r, rule_name) else "", rule_name, color, desc)
            row_count += 1

        body += '<tr><td>基数</td><td><input type="text" name="base_value", value="%s", pattern="^(\d){1,}.?(\d+)?$", ' \
                'title="基数, 单位人民币, 请看倍数说明" /></td></tr>' % (r["base_value"], )
        body += '<tr><td>倍数</td><td><input type="text" name="stock_times", value="%s" pattern="^(\d-){1,}\d$" ' \
                'title="如 0-0-0-1-6 为连续四次符合规则, 第4次设置为基数的1倍, 第5次设置为基数的六倍" /></td></tr>' % \
                (r["stock_times"], )
        body += '<tr><td>时段</td><td><input type="text" name="working_period", value="%s", pattern="^\d\d-\d\d$", ' \
                'title="进行自动购买的时段, 起始小时-结束小时, 00-24为全天, 00-00为不进行购买, 08-12为早上8点至中午12点" />' \
                '</td></tr>' % (r["working_period"], )
        body += "</table>"
        return body, row_count + 3

    def get_stock_info_table(self, r, row_count):
        body = "<table>"
        if not stock_pool:
            body += "<caption><h3>今日还未有结果</h3></caption>"
        else:
            body += "<caption><h3>今日结果</h3></caption>"

        count = 0
        temp_pool = copy.deepcopy(stock_pool)
        rule.paint(r, temp_pool)
        for date, first_ball in temp_pool.items():
            body += "<tr>"
            for ball in first_ball:
                body += '<td' + (' bgcolor="%s">' % (ball.color, ) if ball.color else '>')
                if ball.color == rule.repeat_color:
                    body += '<font bgcolor="%s">%s</font>' % (rule.repeat_font_color, ball.keyword)
                else:
                    body += ball.keyword
                body += "</td>"
            body += "</tr>\n"
            count += 1
            if count > row_count:
                break

        body += "</table>"
        return body
