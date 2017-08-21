import redis
import json
from app.Stock.Config import config, stock_pool

pool = redis.ConnectionPool(host=config["redis"]["host"], port=config["redis"].getint("port"),
                            db=config["redis"].getint("db"), password=config["redis"]["password"])
redis_client = redis.StrictRedis(connection_pool=pool)


def clear_out_date_val():
    pass


def refresh_pool():
    val_str = redis_client.get(config["redis"]["pool_key"])
    stock_pool.update(json.loads(val_str))
    clear_out_date_val()

