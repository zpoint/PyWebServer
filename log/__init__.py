import logging

format_str = "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s"
formatter = logging.Formatter(format_str)


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
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='%s' % (log_dir, ),
                        filemode='w')
    # console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # info
    h1 = logging.FileHandler("%s_info.log" % (log_dir, ), mode="w", encoding="utf8")
    h1.setFormatter(formatter)
    f1 = SingleLevelFilter(logging.INFO, False)
    h1.addFilter(f1)
    rootLogger = logging.getLogger()
    rootLogger.addHandler(h1)

