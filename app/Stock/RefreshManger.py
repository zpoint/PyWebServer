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
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
from threading import Thread

from ConfigureUtil import generate_connector
from app.Stock.StockLogin import login
from app.Stock.StockLogin import StockLogin
from app.Stock.VerifyCodeUtil import VerifyUtilObject
from app.Stock.Rules import rule
from app.Stock.Config import stock_pool, config
from app.Stock.DataBase import DataBaseUtil
from app.Stock.FunctionUtil import generate_cookie, get_cookie_dict, generate_headers


next_buying_pool = dict()
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
        self.verifyUtil = VerifyUtilObject(self.session)

    def run(self):
        self.loop.run_until_complete(self.refresh_main())

    async def refresh_person(self, user_info):
        await asyncio.sleep(random.randint(10, 15), loop=self.loop)  # every one sleep for different second
        if isinstance(user_info["bind_cookie"], str):
            user_info["bind_cookie"] = json.loads(user_info["bind_cookie"])

        url = user_info["prefer_host"] + "/sczzz365482f_10355/klc/order/list/?&_=%s__autorefresh" % \
                                         (int(time.time() * 1000), )
        data = "action=ajax&play=bothSides&ball=&cat=13"
        headers = generate_headers()
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Cookie"] = generate_cookie(user_info["bind_cookie"])
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
                                           post_body["cname"], r["bind_cookie"], session=self.session)

        if not success:
            return False
        else:
            self.db.update_param(r, {}, cookie_dict, False)
            self.db.set_cookie_valid(r)
            return True

    async def re_login_person(self, user_info, retry=5, curr_count=1):
        await asyncio.sleep(random.randint(0, 3), loop=self.loop)  # avoid DDOS
        try:
            img_byte = await StockLogin.get_img_byte(user_info, loop=self.loop, session=self.session)
        except (ValueError, IndexError):
            if curr_count <= retry:
                return await self.re_login_person(user_info, retry, curr_count + 1)
            else:
                # verify code error
                logging.error("Login Fail, Retry %d time, username: %s" % (retry, user_info["username"]))
                return False

        img_b64 = quote(base64.encodebytes(img_byte))
        success, value = await self.verifyUtil.get_verify_value(img_b64)
        if success:
            post_body = dict()
            post_body["verify_code"] = value
            verify_success = await self.re_login(user_info, post_body)
            if verify_success:
                self.verifyUtil.save_img(img_byte, value)
                return verify_success
            else:
                return await self.re_login_person(user_info, retry, curr_count+1)

        elif curr_count <= retry:
            return await self.re_login_person(user_info, retry, curr_count+1)
        else:
            logging.error("Login Fail, Retry %d time, username: %s" % (retry, user_info["username"]))
            return False

    async def buy_with_val(self, user_info, buy_list, retry=3, current=1):
        url = user_info["prefer_host"] + "/sczzz365482f_10355/pk/order/leftInfo/?post_submit=&=&_=%d__ajax" % \
                                         (int(time.time() * 1000), )
        headers = generate_headers()
        headers["Referer"] = user_info["prefer_host"]
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["ajax"] = "true"
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Cookie"] = generate_cookie(user_info["bind_cookie"])
        param = {
            "t": "",
            "v": ""
        }
        for cargo in buy_list:
            param["t"] += "|".join(str(_) for _ in cargo) + ";"
        param["v"] = user_info["buy_step"]
        data = urlencode(param)
        async with self.session.post(url, data=data, headers=headers) as resp:
            text = await resp.text()
            rgx = re.compile('{".+"errors":.+?}(?=ê)', re.DOTALL)
            result = re.search(rgx, text)
            if not result:
                if current > retry:
                    logging.error("User: %s fail buying with val: %s" % (user_info["username"], param["t"]))
                    self.db.set_cookie_invalid(user_info)
                    return False
                else:
                    await asyncio.sleep(random.randint(0, 3), loop=self.loop)
                    return await self.buy_with_val(user_info, buy_list, retry, current+1)

            json_obj = json.loads(result.group(0))
            if json_obj["errors"]:
                if json_obj["data"] and "user" in json_obj["data"] and "version_number" in json_obj["data"]["user"]:
                    user_info["buy_step"] = json_obj["data"]["user"]["version_number"]
                    self.db.update_buy_step(user_info)

                if current > retry:
                    logging.error("User: %s fail buying with val: %s" % (user_info["username"], param["t"]))
                    return False
                else:
                    await asyncio.sleep(random.randint(0, 3), loop=self.loop)
                    return await self.buy_with_val(user_info, buy_list, retry, current+1)

        logging.info("Success buying: %s, username: %s" % (param["t"], user_info["username"]))
        self.db.update_buying_table(user_info, json_obj, buy_list, next_refresh_data[0])
        cookie_dict = get_cookie_dict(resp.cookies)
        if cookie_dict:
            self.db.update_cookie(user_info, cookie_dict)

    async def buy_person(self, user_info):
        await asyncio.sleep(random.randint(0, 5), loop=self.loop)
        if not user_info["running_status"]:
            return True  # no need to buy
        buy_list = list()
        temp_pool = copy.deepcopy(stock_pool)
        rule.paint(user_info, temp_pool)
        times_lst = [float(i) for i in user_info["stock_times"].split("-")]
        base_val = user_info["base_value"]
        prev_buy_dict = dict()
        buy_step_need_forward = False
        if user_info["cargo"]:
            if user_info["cargo_buying_for_date"] == next_refresh_data[0]:
                logging.info("already buy, no need to buy")
                return True

            for item in user_info["cargo"]:
                prev_buy_dict[int(item[0])] = item[1]

        for date, first_ball in temp_pool.items():
            vertical_index = -1
            for ball in first_ball:
                vertical_index += 1
                if vertical_index >= 11:
                    break
                if vertical_index in prev_buy_dict and prev_buy_dict[vertical_index] == ball.keyword:  # bingo
                    user_info["buy_cursor"] = 0
                    user_info["clear_line_cursor"] = rule.count_depth(ball)
                    self.db.update_buy_cursor_and_clear_cursor(user_info)
            break

        for date, first_ball in temp_pool.items():
            vertical_index = -1
            for ball in first_ball:
                vertical_index += 1
                if vertical_index >= 11:
                    break
                if not hasattr(ball, "weight"):  # has no any rule, so ball does not have weight when painted
                    return True
                if ball.weight == 0:
                    continue
                # if ball.weight > len(times_lst):
                #    ball.weight %= len(times_lst)
                if user_info["buy_cursor"] >= len(times_lst):
                    user_info["buy_cursor"] %= len(times_lst)
                buy_val = times_lst[user_info["buy_cursor"]] * base_val
                if buy_val >= 2:
                    buy_list.append(("%03d" % (vertical_index, ), ball.keyword,
                                     next_buying_pool["%03d" % (vertical_index, )][str(ball.keyword)],
                                     "%d" % (buy_val, )))
                else:
                    logging.warning("Incorrect buy val: %d, username: %s, keyword: %s, index: %d, date: %s" %
                                    (buy_val, user_info["username"], ball.keyword, vertical_index, str(date)))
                    logging.warning(str(times_lst) + " " + str(ball.weight) + " buy_cursor: %d, clear_line_cursor: %d"
                                    % (user_info["buy_cursor"], user_info["clear_line_cursor"]))
                    buy_step_need_forward = True
            break

        if buy_list:
            await self.buy_with_val(user_info, buy_list)
            user_info["buy_cursor"] += 1
            self.db.update_buy_cursor(user_info)
        elif buy_step_need_forward:
            user_info["buy_cursor"] += 1
            self.db.clear_cargo(user_info)
            self.db.update_buy_cursor(user_info)
        else:
            self.db.clear_cargo(user_info)
            self.db.update_buy_cursor(user_info)

    async def re_login_all(self):
        re_login_info = self.db.get_info_who_need_re_login()
        if re_login_info:
            tasks = [self.re_login_person(info) for info in re_login_info]
            await asyncio.gather(*tasks, loop=self.loop)

    async def sleep_when_market_closed(self):
        now = datetime.now()
        rest_begin_data = datetime.strptime("%d-%d-%d " % (now.year, now.month, now.day) +
                                            config["common"]["rest_begin_hour"], "%Y-%m-%d %H:%M")
        rest_end_data = datetime.strptime("%d-%d-%d " % (now.year, now.month, now.day) +
                                          config["common"]["rest_end_hour"], "%Y-%m-%d %H:%M")
        if rest_begin_data < now < rest_end_data:
            sleep_seconds = (rest_end_data - now).seconds
            self.db.reset_clear_line_cursor()
            logging.info("Market closed, Going to sleep for %d seconds, is %.2f hours" %
                         (sleep_seconds, sleep_seconds / 3600.0))
            await asyncio.sleep(sleep_seconds, loop=self.loop)

    async def refresh_main(self):
        global next_refresh_data, buy_flag
        while True:
            try:
                # check whether stock marker opened
                await self.sleep_when_market_closed()
                info = self.db.get_info_whose_cookie_is_valid()
                if not info:
                    await self.re_login_all()
                    info = self.db.get_info_whose_cookie_is_valid()
                    if not info:
                        logging.warning("After re login, still no valid cookie to get latest data")
                        await asyncio.sleep(random.randint(10, 15), loop=self.loop)
                        continue

                if not next_refresh_data or datetime.now() > next_refresh_data[0]:
                    await self.get_info_until_success(info)

                if buy_flag or (not next_refresh_data or datetime.now() > next_refresh_data[0]):
                    await self.re_login_all()

                info = self.db.get_info_whose_cookie_is_valid()
                if not info:
                    logging.warning("No valid cookie to get latest data")
                else:
                    tasks = list()
                    logging.info("In the main loop, buy flag: " +
                                 str(buy_flag));
                    if buy_flag:
                        result = await self.get_current_table(random.choice(info))
                        if result is True:
                            for each in info:
                                tasks.append(self.loop.create_task(self.buy_person(each)))
                            buy_flag = False
                        else:
                            logging.error("Unable to get current table")

                    else:
                        for each in info:
                            tasks.append(self.loop.create_task(self.refresh_person(each)))

                    if tasks:
                        await asyncio.wait(tasks, loop=self.loop)

                await asyncio.sleep(random.randint(5, 10), loop=self.loop)
            except Exception as e:
                logging.error(traceback.format_exc())
                await asyncio.sleep(random.randint(10, 15), loop=self.loop)

    async def get_info_until_success(self, info):
        global clear_flag
        for each_info in info:
            result = await self.get_info(each_info)
            if result is True:
                break

        if clear_flag:
            clear_flag = stock_pool.clear_out_date()

    async def get_info(self, user_info):
        global clear_flag, buy_flag
        now = datetime.now()
        if isinstance(user_info["bind_cookie"], str):
            user_info["bind_cookie"] = json.loads(user_info["bind_cookie"])

        url = user_info["prefer_host"] + "/sczzz365482f_10355/pk/result/index"
        post_body = "date=" + now.strftime("%Y-%m-%d")
        headers = generate_headers()
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Cookie"] = generate_cookie(user_info["bind_cookie"])
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["ajax"] = "true"
        headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            prev_refresh_data = next_refresh_data[0] if next_refresh_data else None
            async with self.session.post(url, data=post_body, headers=headers) as resp:
                text = await resp.text()
                rgx = re.compile('{".+"errors":".*?"}', re.DOTALL)
                result = re.search(rgx, text)
                if not result:
                    self.db.set_cookie_invalid(user_info)
                    return False
                json_obj = json.loads(result.group(0))

                if json_obj["data"]["result"] and len(json_obj["data"]["result"]) >= 2:
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

                if json_obj["data"]["result"] and len(json_obj["data"]["result"]) >= 1:
                    logging.info("prev_refresh_data" + str(prev_refresh_data) +
                                 "next_refresh_data" + str(next_refresh_data))
                    if not prev_refresh_data or prev_refresh_data != next_refresh_data[0]:
                        buy_flag = True

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

    async def get_current_table(self, user_info):
        host = user_info["prefer_host"]
        url = host + "/sczzz365482f_10355/pk/order/list?&_=%d__ajax" % (int(time.time() * 1000), )
        body1 = "play=ballNO15"
        body2 = "play=ballNO60"
        headers = generate_headers()
        headers["Host"] = user_info["prefer_host"].replace("http://", "")
        headers["Cookie"] = generate_cookie(user_info["bind_cookie"])
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["ajax"] = "true"
        headers["X-Requested-With"] = "XMLHttpRequest"
        result1, result2 = await asyncio.gather(self.get_current_table_n(user_info, url, body1, headers),
                                                self.get_current_table_n(user_info, url, body2, headers),
                                                loop=self.loop)
        return result1 and result2

    async def get_current_table_n(self, user_info, url, body, headers, retry=3, current=1):
        async with self.session.post(url, data=body, headers=headers) as resp:
            text = await resp.text()
            rgx = re.compile('{".+"errors":".*?"}', re.DOTALL)
            result = re.search(rgx, text)
            if not result:
                self.db.set_cookie_invalid(user_info)
                return False
            json_obj = json.loads(result.group(0))

            cookie_dict = get_cookie_dict(resp.cookies)
            if cookie_dict:
                self.db.update_cookie(user_info, cookie_dict)
            if not json_obj["data"]["integrate"]:
                if current < retry:
                    await asyncio.sleep(random.randint(25, 35), loop=self.loop)
                    return await self.get_current_table_n(user_info, url, body, headers, retry, current+1)
                else:
                    logging.warning("No current_table result")
                    return False

            for k, v in json_obj["data"]["integrate"].items():
                if int(k) > 910:
                    continue
                index = k[:3]
                keyword = k[3:]
                if index not in next_buying_pool:
                    next_buying_pool[index] = {keyword: v}  # next_buying_pool[000][5] = 9.916
                else:
                    next_buying_pool[index][keyword] = v
        return True
