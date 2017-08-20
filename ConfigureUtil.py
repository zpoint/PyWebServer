from aiohttp import web
import aiohttp
import asyncio


def generate_connector(limit=50):
    """
    https://github.com/KeepSafe/aiohttp/issues/883
    if connector is passed to session, it is not available anymore
    """
    return aiohttp.TCPConnector(limit=limit, loop=global_loop)

global_loop = asyncio.get_event_loop()
global_session = aiohttp.ClientSession(connector=generate_connector(), loop=global_loop)


class Headers(object):
    json_headers = {
        "Content-Type": "application/json",
        "charset": "utf-8"
    }

    html_headers = {
        "Content-Type": "text/html",
        "charset": "utf-8"
    }


class JsonError(object):
    param_error = {
        "error": "参数错误"
    }
    empty_result = {
        "error": "搜索请求成功，无结果"
    }


class ErrorReturn(object):
    @staticmethod
    def html(h1, back_to_path, title="Error", body="", headers=None):
        return web.Response(text="""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        </head>
        <title>%s</title>
        <h1 align="center">%s</h1>
        %s
        <p align="center">
        <span id="time">3</span> 秒后跳转</a></p>
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
        </p>
        </html>""" % (title, h1, body, back_to_path), headers=Headers.html_headers if not headers else headers)

    @staticmethod
    def invalid(title="非法访问", to_main=True, main_path="/Stock"):
        if to_main:
            return web.Response(text="""
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
            <html>
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            </head>
            <title>%s</title>
            <h1 align="center">%s</h1>
            <p align="center">
            <span id="time">3</span> 秒后跳转</a></p>
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
            </p>
            </html>
            """ % (title, title, main_path), headers=Headers.html_headers)
        else:
            return web.Response(text="""
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
            <html>
            <head>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            </head>
            <title>%s</title>
            <h1 align="center">%s</h1>
            """ % (title, title), headers=Headers.html_headers)



class WebPageBase(object):
    @staticmethod
    def head(h1=None):
        html = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html>
        <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        </head>
        <title>自动系统</title>
        """
        if h1:
            html += "<h1 align='center'>%s</h1>" % (h1, )
        return html
