import random
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode

from app.Stock.DataBase import DBUtil
from ConfigureUtil import Headers, ErrorReturn


class StockLogin(View):
    path = "/Stock/VerifyCode"
    async def get(self):
        if not DBUtil.valid_user(self.request.headers["Cookie"]):
            return ErrorReturn.invalid()
        html = """
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=gb2312">
        <title>自定义提示</title>
        <script src="jquery-1.8.3.js" type="text/javascript"></script>
        <script src="sAlter.js" type="text/javascript"></script>
        <link href="GetRelationByPhone.css" rel="stylesheet" type="text/css" />
        </head>
        
        <body>
         <div>
              <form id="form1" action="#" method="post">
                <div>
                    <section class="infos">
                    <label class="fLeft">手机号</label>
                    <input type="hidden" value="oLlIXuNocl66hPYHHt8vwAOLhWTA" name="openid" />
                    <span class="commeInput"><input type="text" class="no-border" name="phone" id="phone" value="" placeholder="请输入您的手机号"/>
                    </span>
                    <em id="mob" class="yg-input-close rt12"></em></section>
        
                    <section class="infos no-boder">
                    <label class="fLeft">验证码</label>
                    <span class="commeInput"><input type="text" class="no-border2" name="code" id="code" value="" placeholder="请输入验证码"  />
                    <input type="button" id="btn"  class="btn_mfyzm" value="获取验证码"  onclick="getverify()"    />
                    </span>
                    <em id="mob2" class="yg-input-close lt50"></em></section>
                    <div><button type="button" class="btn-pay" onclick="go()"  title="确定">确&nbsp &nbsp 定</button></div>
                </div>
              </form>
        </div>
        </body>
        </html>
        """
        return web.Response(text=html, headers=Headers.html_headers)
