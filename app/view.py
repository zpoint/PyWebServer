from aiohttp import web
from aiohttp.web import View
from ConfigureUtil import Headers

class MyView(View):
    path = "/"

    async def get(self):
        # return web.Response(text='Hello Aiohttp!')
        body = """<head><meta http-equiv="refresh" content="0;url=/Stock"></head>"""
        return web.Response(text=body, headers=Headers.html_headers)

