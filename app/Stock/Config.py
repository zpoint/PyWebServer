import configparser

config = configparser.ConfigParser()
config.read("app/Stock/config.ini")

stock_pool = dict()
