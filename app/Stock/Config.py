from collections import OrderedDict
import datetime
import configparser

config = configparser.ConfigParser()
config.read("app/Stock/config.ini")


class Ball(object):
    def __init__(self, up, down, left, right, keyword):
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.keyword = keyword
        self.length = 0

    def iter_horizontal(self):
        right = self
        while right is not None:
            yield right
            right = right.right

    def iter_vertical(self):
        down = self
        while down is not None:
            yield down
            down = self.down

    def __len__(self):
        return self.length

    def __iter__(self):
        return self.iter_horizontal()


class StockPoll(object):
    def __init__(self):
        self.bucket = OrderedDict()

    def __setitem__(self, key, words):
        if isinstance(key, str):
            key = datetime.datetime.strptime(key, "%Y-%m-%d - %H:%M")
        if key in self.bucket:
            return  # doesn't handle the case when key the same but value different

        values = list(self.bucket.values())
        down_line = values[0] if values else None

        prev_ball = None
        index = 0
        for word in words:
            up = None
            down = down_line[index] if down_line else None
            left = prev_ball
            right = None
            ball = Ball(up, down, left, right, word)
            if index == 0:
                self.bucket[key] = ball
            if down:
                down.up = ball
            # set right of prev ball
            if prev_ball:
                prev_ball.right = None

            prev_ball = ball
            index += 1

        self.bucket[key].length = index + 1

    def __getitem__(self, item):
        key = datetime.datetime.strptime(item, "%Y-%m-%d - %H:%M") if isinstance(item, str) else item
        return self.bucket[key]

    def clear_out_date(self):
        now = datetime.datetime.now()
        del_keys = list()
        for key in list(self.bucket.values()):
            if now.day != key.day:
                del_keys.append(key)
        for key in del_keys:
            for ball in self.bucket[key]:
                if ball.up is not None:
                    ball.up.down = None
                    ball.up = None
                if ball.down is not None:
                    ball.down.up = None
                    ball.down = None
                if ball.left is not None:
                    ball.left.right = None
                    ball.left = None
            del self.bucket[key]

        return True if del_keys else False

    def __str__(self):
        for date, first_ball in self.bucket.items():
            print(date, end="")
            for ball in first_ball:
                print(ball.keyword, end=" ")
            print("")
        if not self.bucket:
            print("Empty stock_pool")

    def __bool__(self):
        return bool(self.bucket)

    def items(self):
        return self.bucket.items()

stock_pool = StockPoll()
