import re
import aiohttp
import json
import logging
import time
import asyncio
import random
import traceback
import base64
import copy
from datetime import datetime
from urllib.parse import quote
from threading import Thread

from ConfigureUtil import generate_connector
from app.Stock.StockLogin import login
from app.Stock.StockLogin import StockLogin
from app.Stock.VerifyCodeUtil import verifyUtil
from app.Stock.Rules import rule
from app.Stock.Config import stock_pool
from app.Stock.DataBase import DataBaseUtil
from app.Stock.FunctionUtil import generate_cookie, get_cookie_dict, generate_headers

next_refresh_data = list()
clear_flag = False
buy_flag = False


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

    async def re_login(self, r, post_body):
        post_body.update(r["bind_param"])
        post_body["username"] = r["bind_username"]
        post_body["password"] = r["bind_password"]
        keys = ("verify_code", "verify_value", "username", "password", "cid", "cname")
        for key in keys:
            if key not in post_body:
                logging.error("Key: %s not in body, username: %s" % (key, post_body["username"]))
                return False

        success, cookie_dict = await login(r["prefer_host"], post_body["verify_code"], post_body["verify_value"],
                                           post_body["username"], post_body["password"], post_body["cid"],
                                           post_body["cname"], r["bind_cookie"])

        if not success:
            return False
        else:
            self.db.update_param(r, {}, cookie_dict, False)
            self.db.set_cookie_valid(r)
            return True

    async def re_login_person(self, user_info, retry=5, curr_count=1):
        await asyncio.sleep(random.randint(0, 3))  # avoid DDOS
        img_byte = await StockLogin.get_img_byte(user_info)
        img_b64 = quote(base64.encodebytes(img_byte))
        success, value = await verifyUtil.get_verify_value(img_b64)
        if success:
            post_body = dict()
            post_body["verify_code"] = value
            verify_success = await self.re_login(user_info, post_body)
            if verify_success:
                verifyUtil.save_img(img_byte, value)
                return verify_success
            else:
                return self.re_login_person(retry, curr_count+1)

        elif curr_count <= retry:
            return await self.re_login_person(retry, curr_count+1)
        else:
            logging.error("Login Fail, Retry %d time, username: %s" % (retry, user_info["username"]))
            return False

    async def buy_with_val(self, user_info, buy_list):
        pass

    async def buy_person(self, user_info):
        buy_list = list()
        temp_pool = copy.deepcopy(stock_pool)
        rule.paint(user_info, temp_pool)
        times_lst = [float(i) for i in user_info["stock_times"].split("-")]
        base_val = user_info["base_value"]

        for date, first_ball in temp_pool.items():
            for ball in first_ball:
                if ball.weight == 0:
                    continue
                if ball.weight > len(times_lst):
                    ball.weight %= len(times_lst)
                buy_val = times_lst[ball.weight - 1] * base_val
                if buy_val > 2:
                    buy_list.append((date, ball.keyword, buy_val))
                else:
                    logging.error("Error buy val, username: %s, keyword: %s, date: %s" % (user_info["username"],
                                                                                          ball.keyword, str(date)))
            break
        if buy_list:
            await self.buy_with_val(user_info, buy_list)

    async def refresh_main(self):
        global next_refresh_data, buy_flag
        while True:
            try:
                if buy_flag:
                    re_login_info = self.db.get_info_who_need_re_login()
                    if re_login_info:
                        tasks = [self.re_login_person(info) for info in re_login_info]
                        await asyncio.gather(*tasks, loop=self.loop)

                info = self.db.get_info_whose_cookie_is_valid()
                if not info:
                    logging.warning("No valid cookie to get latest data")
                    await asyncio.sleep(random.randint(10, 15), loop=self.loop)
                else:
                    tasks = list()
                    if buy_flag:
                        for each in info:
                            tasks.append(self.loop.create_task(self.buy_person(each)))
                        buy_flag = False

                    else:
                        for each in info:
                            tasks.append(self.loop.create_task(self.refresh_person(each)))

                    if not next_refresh_data or datetime.now() > next_refresh_data[0]:
                        tasks.append(self.get_info_until_success(info))
                    await asyncio.wait(tasks, loop=self.loop)

            except Exception as e:
                logging.error(traceback.format_exc())
                await asyncio.sleep(random.randint(10, 15), loop=self.loop)

    async def get_info_until_success(self, info):
        global clear_flag
        for each_info in info:
            result = await self.get_info(each_info)
            if result is True:
                if clear_flag:
                    clear_flag = stock_pool.clear_out_date()

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

                if json_obj["data"]["result"] and len(json_obj["data"]["result"]) > 2:
                    global clear_flag

                    if not json_obj["data"]["result"][0][2]:  # the latest date has empty result
                        return False

                    prev_date = datetime.strptime(str(now.year) + "-" + json_obj["data"]["result"][1][1],
                                                  "%Y-%m-%d - %H:%M")
                    curr_date = datetime.strptime(str(now.year) + "-" + json_obj["data"]["result"][0][1],
                                                  "%Y-%m-%d - %H:%M")
                    if not next_refresh_data:
                        next_refresh_data.append(curr_date + (curr_date - prev_date))
                    else:
                        next_refresh_data[0] = curr_date + (curr_date - prev_date)

                    if next_refresh_data[0].day != curr_date.day:
                        clear_flag = True
                    logging.info("next_refresh_data " + str(next_refresh_data[0]))

                json_obj["data"]["result"].reverse()  # sort before insert

                for each_result in json_obj["data"]["result"]:
                    stock_pool[str(now.year) + "-" + each_result[1]] = each_result[2:]

                cookie_dict = get_cookie_dict(resp.cookies)
                if cookie_dict:
                    self.db.update_cookie(user_info, cookie_dict)
                return True
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error("Unable to get_info for userid: %s, username: %s" % (user_info["userid"],
                                                                               user_info["username"]))
