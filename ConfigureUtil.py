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


class Headers:
    json_headers = {
        "Content-Type": "application/json",
        "charset": "utf-8"
    }


class JsonError:
    param_error = {
        "error": "参数错误"
    }
    empty_result = {
        "error": "搜索请求成功，无结果"
    }