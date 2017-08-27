from aiohttp import web
from ConfigureUtil import config
from routes import setup_routes

app = web.Application()
setup_routes(app)
web.run_app(app, host=config["main"]["host"], port=config["main"].getint("port"))
