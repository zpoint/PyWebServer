from aiohttp import web
from aiohttp.web import View


class JsonSchema(View):
    path = "/jsonSchema"

    async def get(self):
        return web.Response(text="jsonSchema")

