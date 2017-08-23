import aiohttp
import asyncio
import random
import time
from ConfigureUtil import global_loop, global_session
from app.Stock.FunctionUtil import generate_cookie, get_cookie_dict, generate_headers


async def fa():
    return 3
    while True:
        s = random.randint(0, 3)
        print("In fa, sleep for ", s)
        await asyncio.sleep(s)

async def fb():
    while True:
        s = random.randint(0, 4)
        print("In fb, sleep for ", s)
        await asyncio.sleep(s)

async def calla():
    return 3


async def main():
    tasks = [global_loop.create_task(calla()), global_loop.create_task(fb())]
    r = await asyncio.wait(tasks, timeout=3)
    for i in r[0]:
        print(i.result())
    await asyncio.wait([i for i in r[1]])

if __name__ == "__main__":
    global_loop.run_until_complete(main())
