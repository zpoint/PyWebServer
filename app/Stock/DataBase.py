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
client = MySQLdb.connect(host=db_config["host"], port=db_config.getint("port"), user=db_config["user"],
                         passwd=db_config["password"], db=db_config["db"])
cursor = client.cursor(MySQLdb.cursors.DictCursor)


def extend_ip(original_ip, new_ip):
    ips = original_ip.split(":")
    if new_ip not in ips:
        ips.append(new_ip)
    return ":".join(ips)


def get_inviting_code(username, password):
    return hashlib.md5((username + password).encode("utf8")).hexdigest()[:4]


def generate_cookie(query_dict):
    return hashlib.md5((str(query_dict) + str(random.randint(0, 10))).encode("utf8")).hexdigest()


class DBUtil(object):
    @staticmethod
    def get_and_reset_cookie(username, password, ip, retry=0):
        query = 'SELECT * FROM user_info WHERE username="%s"' % (username, )
        r = cursor.execute(query)
        if r == 0:
            return False, "该用户不存在"
        r = cursor.fetchone()
        if password != r["password"]:
            return False, "用户名或密码不正确"
        if username == r["username"]:
            cookie = generate_cookie(r)
            query = 'UPDATE user_info SET cookie="%s", ip="%s", last_active_time=%s WHERE userid="%d"' % \
                    (cookie, extend_ip(r["ip"], ip), "now()", r["userid"])
            cursor.execute(query)
            client.commit()
            return True, cookie
        else:  # interrupt by other concurrency request
            retry += 1
            if retry > 3:
                return False, "服务器繁忙, 请稍后再试"
            else:
                return DBUtil.get_and_reset_cookie(username, password, ip, retry)

    @staticmethod
    def valid_user(cookie, return_key=None):
        if "StockID" not in cookie:
            return False

        query = 'SELECT * FROM user_info WHERE cookie="%s"' % (cookie["StockID"], )
        r = cursor.execute(query)
        if r == 0:
            return False
        r = cursor.fetchone()

        if r["bind_cookie"]:
            r["bind_cookie"] = json.loads(r["bind_cookie"])
        if r["bind_param"]:
            r["bind_param"] = json.loads(r["bind_param"])

        if return_key is True:  # return all info
            return r
        return r[return_key] if return_key and return_key in r else True

    @staticmethod
    def bind(r, post_body):
        query = 'UPDATE user_info SET bind_username="%s", bind_password="%s" WHERE userid=%d' % (post_body["username"],
                                                                                                 post_body["password"],
                                                                                                 r["userid"])
        cursor.execute(query)
        client.commit()

    @staticmethod
    def create_user(username, password, invite_code, ip):
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
                'inviting_code) VALUES("%s", "%s", %s, "%s", "%s", "%s", "%s", "%s"); ' % \
                (username, password, "now()", ip, (datetime.datetime.now() + datetime.timedelta(days=free_days)).
                 strftime("%Y-%m-%d %H:%M:%S"), invite_code, config["remote"]["prefer_host"],
                 get_inviting_code(username, password))
        try:
            cursor.execute(query)
        except _mysql_exceptions.IntegrityError as e:
            logging.info(str(e))
            return False, "该用户名已经被注册"

        client.commit()
        return True, "注册成功, 请登录"

    @staticmethod
    def update_param(r, param_dict, cookie_dict, commit=True):
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
        cursor.execute(query)
        if commit:
            client.commit()
