"""
global_loop = asyncio.get_event_loop()

def generate_connector(limit=50):
    #  https://github.com/KeepSafe/aiohttp/issues/883
    #  if connector is passed to session, it is not available anymore
    return aiohttp.TCPConnector(limit=limit, loop=global_loop)

session = aiohttp.ClientSession(connector=generate_connector(), loop=global_loop)
"""