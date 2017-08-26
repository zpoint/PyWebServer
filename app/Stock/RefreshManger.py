import re
import aiohttp
import json
import logging
import time
import asyncio
import random
from datetime import datetime
from threading import Thread
from ConfigureUtil import generate_connector
from app.Stock.Config import stock_pool
from app.Stock.DataBase import DataBaseUtil
from app.Stock.FunctionUtil import generate_cookie, get_cookie_dict, generate_headers

next_refresh_data = None
clear_flag = False


class RefreshMgr(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.loop = asyncio.new_event_loop()
        self.session = aiohttp.ClientSession(connector=generate_connector(loop=self.loop), loop=self.loop)
        self.db = DataBaseUtil()

    def run(self):
        self.loop.run_until_complete(self.refresh_main())

    async def refresh_person(self, user_info):
        await asyncio.sleep(random.randint(10, 15), loop=self.loop)  # every one sleep for different second
        url = user_info["prefer_host"] + "/sscbz3547472f_10355/klc/order/list/?&_=%s__autorefresh" % \
                                         (int(time.time() * 1000), )
        data = "action=ajax&play=bothSides&ball=&cat=13"
        headers = generate_headers()
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Cookie"] = generate_cookie(json.loads(user_info["bind_cookie"]))
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["ajax"] = "true"
        headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            async with self.session.post(url, data=data, headers=headers) as resp:
                text = await resp.text()
                if "ValidatorAlertScript" in text:
                    self.db.set_cookie_invalid(user_info)
                    return False
                else:
                    cookie_dict = get_cookie_dict(resp.cookies)
                    if cookie_dict:
                        self.db.update_cookie(user_info, cookie_dict)

        except Exception as e:
            logging.error(str(e))
            logging.error("username: %s, userid: %d Unable to get cookie" % (user_info["username"], user_info["userid"]))
            return False
        logging.info("username: %s, userid: %d update cookie" % (user_info["username"], user_info["userid"]), )
        return True

    async def refresh_main(self):
        while True:
            try:
                info = self.db.get_info_whose_cookie_is_valid()
                if not info:
                    logging.warning("No valid cookie to get latest data")
                    await asyncio.sleep(random.randint(10, 15), loop=self.loop)
                else:
                    tasks = list()
                    for each in info:
                        tasks.append(self.loop.create_task(self.refresh_person(each)))
                    if next_refresh_data is None or datetime.now() > next_refresh_data:
                        tasks.append(self.get_info_until_success(info))
                    await asyncio.wait(tasks, loop=self.loop)

            except Exception as e:
                logging.error(str(e))
                await asyncio.sleep(random.randint(10, 15), loop=self.loop)

    async def get_info_until_success(self, info):
        global clear_flag
        for each_info in info:
            result = await self.get_info(each_info)
            print("After get result")
            print(stock_pool)
            if result is True:
                if clear_flag:
                    clear_flag = stock_pool.clear_out_date()
                # buy here
                # buy done
                print("After clear")
                print(stock_pool)

    async def get_info(self, user_info):
        now = datetime.now()
        url = user_info["prefer_host"] + "/sscbz3547472f_10355/pk/result/index"
        post_body = "date=" + now.strftime("%Y-%m-%d")
        headers = generate_headers()
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Cookie"] = generate_cookie(json.loads(user_info["bind_cookie"]))
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["ajax"] = "true"
        headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            async with self.session.post(url, data=post_body, headers=headers) as resp:
                text = await resp.text()
                rgx = re.compile('{".+"errors":".*?"}', re.DOTALL)
                result = re.search(rgx, text)
                if not result:
                    self.db.set_cookie_invalid(user_info)
                    return False
                json_obj = json.loads(result.group(0))

                json_obj["data"]["result"].reverse()  # sort before insert
                for each_result in json_obj["data"]["result"]:
                    stock_pool[str(now.year) + "-" + each_result[1]] = each_result[2:]

                cookie_dict = get_cookie_dict(resp.cookies)
                if cookie_dict:
                    self.db.update_cookie(user_info, cookie_dict)

                if json_obj["data"]["result"] and len(json_obj["data"]["result"]) > 2:
                    global next_refresh_data, clear_flag
                    prev_date = datetime.strptime(str(now.year) + "-" + json_obj["data"]["result"][1][1],
                                                  "%Y-%m-%d - %H:%M")
                    curr_date = datetime.strptime(str(now.year) + "-" + json_obj["data"]["result"][0][1],
                                                  "%Y-%m-%d - %H:%M")
                    next_refresh_data = curr_date + (curr_date - prev_date)
                    if next_refresh_data.day != curr_date.day:
                        clear_flag = True
                    logging.info("next_refresh_data " + str(next_refresh_data))
                return True
        except Exception as e:
            logging.error(str(e))
            logging.error("Unable to get_info for userid: %s, username: %s" % (user_info["userid"], user_info["username"]))
