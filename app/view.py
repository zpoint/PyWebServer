from aiohttp import web
from aiohttp.web import View


class MyView(View):
    path = "/"

    async def get(self):
        return web.Response(text='Hello Aiohttp!')

