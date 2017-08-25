from collections import OrderedDict


class Rules(object):
    repeat_color = "#FFFFFF"

    all_rules = OrderedDict([
        ("down", (1, "下", "#33FF00")),  # rule name: (value, description, color)   绿
        ("down_left", (1 << 1, "下左", "	#FF0000")),  # 红
        ("down_right", (1 << 2, "下右", "#0000FF")),  # 蓝
    ])

    def up_up(self):
        pass

    def up_left(self):
        pass

    def up_right(self):
        pass

    def has_rule(self, r, rule_name):
        val, _ = self.all_rules[rule_name]
        return r["rules"] & val

rule = Rules()
