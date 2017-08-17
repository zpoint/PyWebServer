import MySQLdb

from app.Stock.Config import config
db_config = config["mysql"]
client = MySQLdb.connect(host=db_config["host"], port=db_config.getint("port"), user=db_config["user"],
                         passwd=db_config["password"], db=db_config["db"])
cursor = client.cursor()


class DBUtil(object):
    @staticmethod
    def get_and_reset_cookie(username, password):
        # return False, "该用户不存在"
        return True, "1232343"

    @staticmethod
    def isbind(cookie):
        return False

    @staticmethod
    def get_usr_info(cookie):
        return dict()

    @staticmethod
    def valid_user(cookie):
        return True

    @staticmethod
    def bind(cookie, post_body):
        pass

    @staticmethod
    def create_user(username, password, invite_code):
        if not username:
            return False, "请输入用户名"
        if not password:
            return False, "请输入密码"
        if len(password) < 6:
            return False, "密码过短"
        if not invite_code:
            return False, "请输入邀请码"

