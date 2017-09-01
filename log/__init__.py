import logging
from logging.handlers import RotatingFileHandler
from ConfigureUtil import config

format_str = "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s"
formatter = logging.Formatter(format_str)
max_log_file_bytes = config["main"].getint("log_byte")


class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        super(SingleLevelFilter, self).__init__()
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return record.levelno != self.passlevel
        else:
            return record.levelno == self.passlevel


def init_log(log_dir):
    root_logger = logging.getLogger()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='%s' % (log_dir, ),
                        filemode='w')
    # console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # info
    h1 = RotatingFileHandler("%s_info.log" % (log_dir, ), mode="a+", maxBytes=max_log_file_bytes,
                             encoding="utf8", backupCount=1)
    h1.setFormatter(formatter)
    f1 = SingleLevelFilter(logging.INFO, False)
    h1.addFilter(f1)
    root_logger.addHandler(h1)

    # warning
    h1 = RotatingFileHandler("%s_error.log" % (log_dir, ), mode="a+", maxBytes=max_log_file_bytes,
                             encoding="utf8", backupCount=1)
    h1.setFormatter(formatter)
    f1 = SingleLevelFilter(logging.WARNING, False)
    h1.addFilter(f1)
    root_logger.addHandler(h1)
