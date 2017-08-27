from collections import OrderedDict


class Rules(object):
    repeat_color = "#000000"
    repeat_font_color = "#FFFFFF"

    all_rules = OrderedDict([
        ("down", (1, "下", "#33FF00")),  # rule name: (value, description, color)   绿
        ("down_left", (1 << 1, "下左", "	#FF0000")),  # 红
        ("down_right", (1 << 2, "下右", "#0000FF")),  # 蓝
    ])

    def down(self, ball):
        color = self.all_rules[self.down.__name__][2]
        self.repeat_color = color
        if ball.down is not None and ball.keyword == ball.down.keyword:
            ball.color = self.repeat_color if ball.color else color
            ball.down.color = self.repeat_color if ball.down.color else color

    def down_left(self, ball):
        color = self.all_rules[self.down_left.__name__][2]
        self.repeat_color = color
        if (ball.down is not None) and (ball.down.left is not None) and ball.down.keyword == ball.down.left.keyword:
            ball.down.color = self.repeat_color if ball.down.color else color
            ball.down.left.color = self.repeat_color if ball.down.left.color else color

    def down_right(self, ball):
        color = self.all_rules[self.down_right.__name__][2]
        self.repeat_color = color
        if (ball.down is not None) and (ball.down.right is not None) and ball.down.keyword == ball.down.right.keyword:
            ball.down.color = self.repeat_color if ball.down.color else color
            ball.down.right.color = self.repeat_color if ball.down.right.color else color

    def has_rule(self, r, rule_name):
        val, _, __ = self.all_rules[rule_name]
        return r["rules"] & val

    def paint(self, r, stock_pool):
        rule_func = list()
        for rule_name, values in self.all_rules.items():
            if self.has_rule(r, rule_name):
                rule_func.append(getattr(self, rule_name))

        if not rule_func:
            return stock_pool

        for date, first_ball in stock_pool.items():
            for ball in first_ball:
                for paint_func in rule_func:
                    paint_func(ball)

    def get_rule_val(self, rule_lst):
        val = 0
        for name in rule_lst:
            if name in self.all_rules:
                val |= self.all_rules[name][0]
        return val

rule = Rules()
