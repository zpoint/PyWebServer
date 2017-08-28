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
        self.color = None
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

    def __getitem__(self, item):
        index = 0
        ball = self
        while index < item:
            ball = ball.right
            index += 1
        return ball

    def __len__(self):
        return self.length

    def __iter__(self):
        return self.iter_horizontal()

    def __bool__(self):
        return True


class StockPoll(object):
    def __init__(self):
        self.bucket = OrderedDict()

    def __setitem__(self, key, words):
        if isinstance(key, str):
            key = datetime.datetime.strptime(key, "%Y-%m-%d - %H:%M")
        if key in self.bucket:
            return  # doesn't handle the case when key the same but value different
        if words[0] == "":
            return

        keys = list(self.bucket.keys())
        down_line = self.bucket[keys[-1]] if keys else None
        prev_ball = None
        index = 0
        for word in words:
            up = None
            down = down_line[index] if down_line is not None else None
            left = prev_ball
            right = None
            ball = Ball(up, down, left, right, str(word))
            if index == 0:
                self.bucket[key] = ball
            if down:
                down.up = ball
            # set right of prev ball
            if prev_ball is not None:
                prev_ball.right = ball

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
                self.clear_reference(ball)
            del self.bucket[key]

        return True if del_keys else False

    def __str__(self):
        body = ""
        for date, first_ball in self.bucket.items():
            body += str(date) + " "
            for ball in first_ball:
                body += ball.keyword + " "
            body += "\n"
        if not self.bucket:
            body = "Empty stock_pool"
        return body

    def __bool__(self):
        return bool(self.bucket)

    def items(self):
        keys = list(self.bucket.keys())
        keys.reverse()
        for k in keys:
            yield k, self.bucket[k]

    @staticmethod
    def clear_reference(ball):
        if ball.up is not None:
            ball.up.down = None
            ball.up = None
        if ball.down is not None:
            ball.down.up = None
            ball.down = None
        if ball.left is not None:
            ball.left.right = None
            ball.left = None

    def __deepcopy__(self, memo):
        new_pool = StockPoll()
        keys = list(self.bucket.keys())

        for key in keys:
            words = list()
            first_ball = self.bucket[key]
            for ball in first_ball:
                words.append(ball.keyword)
            new_pool[key] = words
        return new_pool

    def __del__(self):
        for key in list(self.bucket.keys()):
            for ball in self.bucket[key]:
                self.clear_reference(ball)
            del self.bucket[key]

stock_pool = StockPoll()
