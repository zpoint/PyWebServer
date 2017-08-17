from app.Stock.DataBase import DBUtil


class Config(object):
    Host = "http://pc12.sss11.us"
    systemVersion = "4_6"


class HtmlBase(object):
    @staticmethod
    def user_info(cookie):
        info = DBUtil.get_usr_info(cookie)
        pass
