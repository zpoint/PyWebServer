import logging
from collections import OrderedDict


class Rules(object):
    repeat_color = "#000000"
    repeat_font_color = "#FFFFFF"
    init_rule_val = 0

    all_rules = OrderedDict([
        ("down", (1, "下", "#33FF00")),  # rule name: (value, description, color)   绿
        ("down_left", (1 << 1, "下左", "	#FF0000")),  # 红
        ("down_right", (1 << 2, "下右", "#0000FF")),  # 蓝
    ])

    @staticmethod
    def count_depth(ball):
        depth = 0
        down = ball
        while down:
            depth += 1
            down = down.down
        return depth

    def set_recursive_val(self, paint_func, ball, clear_line_cursor):
        if ball.color and ball.keyword.isdigit():
            total_depth = self.count_depth(ball)
            depth = 0
            need_continue = True
            row_colored = True
            weight = 0
            current_ball = ball
            delta_depth = total_depth - clear_line_cursor
            if delta_depth < 0:
                logging.error("delta_depth < 0, total_depth: %d, clear_line_cursor: %d" % (total_depth, clear_line_cursor))
            else:
                logging.info("delta_depth: %d " % (delta_depth, ))
            while need_continue:
                depth += 1
                # print("ball", ball.keyword, "depth: ", depth, "delta_depth", delta_depth)
                if depth >= delta_depth:
                    need_continue = False

                if row_colored:
                    weight += 1

                row_colored = False
                next_row_ball = current_ball.down
                if not next_row_ball:
                    break
                left = right = next_row_ball
                while left:
                    if left.color and left.keyword.isdigit():
                        row_colored = True
                        break
                    left = left.left
                while right:
                    if right.color and right.keyword.isdigit():
                        row_colored = True
                        break
                    right = right.right
                    
                current_ball = next_row_ball

            ball.weight = weight - 1 if weight > 0 else weight
        else:
            ball.weight = 0
        print("ball.keyword", ball.keyword, "ball.weight", ball.weight, "delta_depth", self.count_depth(ball) - clear_line_cursor)

    def down(self, ball, return_next=False):
        if return_next:
            return ball.down

        color = self.all_rules[self.down.__name__][2]
        self.repeat_color = color
        if ball.down is not None and ball.keyword == ball.down.keyword:
            ball.color = self.repeat_color if ball.color else color
            ball.down.color = self.repeat_color if ball.down.color else color

    def down_left(self, ball, return_next=False):
        if return_next:
            if ball.down:
                return ball.down.left
            return ball.down

        color = self.all_rules[self.down_left.__name__][2]
        self.repeat_color = color
        if (ball.down is not None) and (ball.down.left is not None) and ball.down.keyword == ball.down.left.keyword:
            ball.down.color = self.repeat_color if ball.down.color else color
            ball.down.left.color = self.repeat_color if ball.down.left.color else color

    def down_right(self, ball, return_next=False):
        if return_next:
            if ball.down:
                return ball.down.right
            return ball.down

        color = self.all_rules[self.down_right.__name__][2]
        self.repeat_color = color
        if (ball.down is not None) and (ball.down.right is not None) and ball.down.keyword == ball.down.right.keyword:
            ball.down.color = self.repeat_color if ball.down.color else color
            ball.down.right.color = self.repeat_color if ball.down.right.color else color

    def has_rule(self, r, rule_name):
        val, _, __ = self.all_rules[rule_name]
        return r["rules"] & val

    def paint(self, r, stock_pool):
        print("paint")
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

        for date, first_ball in stock_pool.items():
            for ball in first_ball:
                for paint_func in rule_func:
                    self.set_recursive_val(paint_func, ball, r["clear_line_cursor"])
            # only need for first line
            break
        return stock_pool

    def get_rule_val(self, rule_lst):
        val = 0
        for name in rule_lst:
            if name in self.all_rules:
                val |= self.all_rules[name][0]
        return val


rule = Rules()
