import datetime
import logging
import hashlib
import random
import json
import MySQLdb.cursors
import _mysql_exceptions

from app.Stock.Config import config

free_days = int(config["common"]["free_days"])
db_config = config["mysql"]


def extend_ip(original_ip, new_ip):
    ips = original_ip.split(":")
    if new_ip not in ips:
        ips.append(new_ip)
    return ":".join(ips)


def get_inviting_code(username, password):
    return hashlib.md5((username + password).encode("utf8")).hexdigest()[:4]


def generate_cookie(query_dict):
    return hashlib.md5((str(query_dict) + ":".join(str(random.randint(0, 100)) for _ in range(100))).
                       encode("utf8")).hexdigest()


class DataBaseUtil(object):
    def __init__(self):
        self.client = MySQLdb.connect(host=db_config["host"], port=db_config.getint("port"), user=db_config["user"],
                                      passwd=db_config["password"], db=db_config["db"])
        self.cursor = self.client.cursor(MySQLdb.cursors.DictCursor)
        self.cursor.execute('SET GLOBAL max_allowed_packet=67108864')
        self.client.commit()

    def get_and_reset_cookie(self, username, password, ip, retry=0):
        query = 'SELECT * FROM user_info WHERE username="%s"' % (username, )
        r = self.execute(query)
        self.commit()
        if r == 0:
            return False, "该用户不存在"
        r = self.cursor.fetchone()
        if password != r["password"]:
            return False, "用户名或密码不正确"
        if username == r["username"]:
            cookie = generate_cookie(r)
            query = 'UPDATE user_info SET cookie="%s", ip="%s", last_active_time=%s WHERE userid="%d"' % \
                    (cookie, extend_ip(r["ip"], ip), "now()", r["userid"])
            self.execute_and_commit(query)
            return True, cookie
        else:  # interrupt by other concurrency request
            retry += 1
            if retry > 3:
                return False, "服务器繁忙, 请稍后再试"
            else:
                return DBUtil.get_and_reset_cookie(username, password, ip, retry)

    def valid_user(self, cookie, return_key=None):
        if "StockID" not in cookie:
            return False

        query = 'SELECT * FROM user_info WHERE cookie="%s"' % (cookie["StockID"], )
        r = self.execute(query)
        self.commit()
        if r == 0:
            return False

        r = self.cursor.fetchone()

        if r["cookie"] != cookie["StockID"]:
            return False

        if r["bind_cookie"]:
            r["bind_cookie"] = json.loads(r["bind_cookie"])
        if r["bind_param"]:
            r["bind_param"] = json.loads(r["bind_param"])
        if r["buy_table"]:
            r["buy_table"] = json.loads(r["buy_table"])

        if return_key is True:  # return all info
            return r
        return r[return_key] if return_key and return_key in r else True

    def bind(self, r, post_body):
        query = 'UPDATE user_info SET bind_username="%s", bind_password="%s", remote_valid=TRUE  WHERE userid=%d' % \
                (post_body["username"], post_body["password"], r["userid"])
        self.execute_and_commit(query)

    def create_user(self, username, password, invite_code, ip):
        if not username:
            return False, "请输入用户名"
        if not password:
            return False, "请输入密码"
        if len(password) < 6:
            return False, "密码过短"
        if not invite_code:
            return False, "请输入邀请码"
        if invite_code != config["common"]["invite_code"]:
            return False, "邀请码不正确"
        query = 'INSERT INTO user_info (username, password, last_active_time, ip, expired, invite_code, prefer_host, ' \
                'inviting_code, stock_times, working_period) VALUES ' \
                '("%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s"); ' % \
                (username, password, "now()", ip, (datetime.datetime.now() + datetime.timedelta(days=free_days)).
                 strftime("%Y-%m-%d %H:%M:%S"), invite_code, config["remote"]["prefer_host"],
                 get_inviting_code(username, password), "0-0-0-0-0", "00-24")
        try:
            self.execute_and_commit(query)
        except _mysql_exceptions.IntegrityError as e:
            logging.info(str(e))
            return False, "该用户名已经被注册"

        self.commit()
        return True, "注册成功, 请登录"

    def update_param(self, r, param_dict, cookie_dict, commit=True):
        if r["bind_param"]:
            r["bind_param"].update(param_dict)
        else:
            r["bind_param"] = param_dict

        if r["bind_cookie"]:
            r["bind_cookie"].update(cookie_dict)
        else:
            r["bind_cookie"] = cookie_dict

        param_dict = r["bind_param"]
        cookie_dict = r["bind_cookie"]

        query = "UPDATE user_info SET bind_param='%s', bind_cookie='%s' WHERE userid=%d" % \
                (json.dumps(param_dict), json.dumps(cookie_dict), r["userid"])
        self.execute_and_commit(query)
        if commit:
            self.commit()

    def update_cookie(self, r, cookie_dict):
        if r["bind_cookie"]:
            original_cookie = json.loads(r["bind_cookie"]) if isinstance(r["bind_cookie"], str) else r["bind_cookie"]
            original_cookie.update(cookie_dict)
        else:
            original_cookie = cookie_dict
        query = "UPDATE user_info SET bind_cookie='%s' WHERE userid=%d" % (json.dumps(original_cookie), r["userid"])
        self.execute_and_commit(query)

    def get_info_whose_cookie_is_valid(self):
        query = "SELECT * from user_info WHERE remote_valid=TRUE"
        self.execute_and_commit(query)
        results = self.cursor.fetchall()
        for r in results:
            if r["bind_cookie"]:
                r["bind_cookie"] = json.loads(r["bind_cookie"])
            if r["bind_param"]:
                r["bind_param"] = json.loads(r["bind_param"])
            if r["buy_table"]:
                r["buy_table"] = json.loads(r["buy_table"])
        return results

    def get_info_who_need_re_login(self):
        query = "SELECT * from user_info WHERE remote_valid=FALSE AND force_login=TRUE"
        self.execute_and_commit(query)
        results = self.cursor.fetchall()
        for r in results:
            if r["bind_cookie"]:
                r["bind_cookie"] = json.loads(r["bind_cookie"])
            if r["bind_param"]:
                r["bind_param"] = json.loads(r["bind_param"])
            if r["buy_table"]:
                r["buy_table"] = json.loads(r["buy_table"])
        return results

    def set_cookie_invalid(self, r):
        query = 'UPDATE user_info SET remote_valid=FALSE WHERE userid=%d' % (r["userid"], )
        self.execute_and_commit(query)

    def set_cookie_valid(self, r):
        query = 'UPDATE user_info SET remote_valid=TRUE WHERE userid=%d' % (r["userid"], )
        self.execute_and_commit(query)

    def check_cookie_valid(self, r):
        query = "SELECT remote_valid FROM user_info WHERE userid=%d" % (r["userid"], )
        self.execute_and_commit(query)
        return self.cursor.fetchone()["remote_valid"]

    def update_base(self, r, new_rule_val, new_base_val, new_stock_val, new_period, new_status):
        if r["rules"] == new_rule_val and r["base_value"] == new_base_val and r["stock_times"] == new_stock_val and \
                        r["working_period"] == new_period and r["running_status"] == new_status:
            return
        query = 'UPDATE user_info SET rules=%d, base_value=%d, stock_times="%s", working_period="%s", running_status=' \
                '%s WHERE userid=%d' % (new_rule_val, new_base_val, new_stock_val,
                                        new_period, new_status, r["userid"])

        self.execute_and_commit(query)
        r["rules"] = new_rule_val
        r["base_value"] = new_base_val
        r["stock_times"] = new_stock_val
        r["working_period"] = new_period
        r["running_status"] = new_status

    def update_buying_table(self, r, json_obj):
        date_now_str = datetime.datetime.now().strftime("%Y-%m-%d")
        for i in json_obj["data"]["user"]["new_orders"]:
            i[-1] = date_now_str + " " + i[-1]

        query = "UPDATE user_info SET buy_table='%s' WHERE userid=%d" % (json.dumps(json_obj), r["userid"])
        self.execute_and_commit(query)

    def update_buy_step(self, r):
        query = 'UPDATE user_info SET buy_step=%d WHERE userid=%d' % (int(r["buy_step"]), r["userid"])
        self.execute_and_commit(query)

    def execute_and_commit(self, query):
        try:
            self.cursor.execute(query)
            self.client.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.__init__()
            self.cursor.execute(query)
            self.client.commit()

    def execute(self, query):
        try:
            return self.cursor.execute(query)
        except (AttributeError, MySQLdb.OperationalError):
            self.__init__()
            return self.cursor.execute(query)

    def commit(self):
        try:
            self.client.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.__init__()
            self.client.commit()

DBUtil = DataBaseUtil()
