import json
import logging
from aiohttp import web
from aiohttp.web import View
from urllib.parse import urlencode
from ConfigureUtil import Headers, JsonError, global_session

GET_COOKIES_URL = 'http://i.waimai.meituan.com/home?lat=29.92683&lng=119.43733'
get_cookie_url = 'http://i.waimai.meituan.com/home?lat=22.540667&lng=114.047671'
base_url = 'http://i.waimai.meituan.com/ajax/v6/poi/filter?lat=23.207669&lng==113.219207&_token='
base_param = {
    "SQ_CALENDAR_VIEW": "day",
    "SQ_CALENDAR_DATE": "2017-04-27"
}

headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN, en-US',
        'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': "",
        'Host': 'i.waimai.meituan.com',
        'Origin': 'http://i.waimai.meituan.com',
        'Referer': 'http://i.waimai.meituan.com/home?lat=22.540667&lng=114.047671',
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.1; zh-cn; Google Nexus 7 - 4.1.1 - API 16 - 800x1280 Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30',
        'X-Requested-With': 'XMLHttpRequest',
    }

GET_COOKIES_HEADER = {
    "Host": "i.waimai.meituan.com",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch",
    "Accept-Language": "zh-CN,zh;q=0.8",
}

get_cookie_header = {
    "Host": "i.waimai.meituan.com"
}

first_time = True


class MeituanWM(View):
    path = "/restaurant/meituanwm"

    async def get_cookie(self):
        logging.info(get_cookie_url)
        async with global_session.get(GET_COOKIES_URL) as response:
            text = await response.text()
            print(text)
            print(response)
            print(dir(response))
            print("cookies", response.headers)

    async def get_result(self):
        global first_time
        if first_time:
            await self.get_cookie()
            first_time = False

    async def get(self):
        return await self.get_result()

