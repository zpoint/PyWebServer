from collections import OrderedDict


class Rules(object):
    all_rules = OrderedDict([
        ("up_up", (1, "上上")),  # rule name: (value, description)
        ("up_left", (1 << 1, "上左")),
        ("up_right", (1 << 2, "上右")),
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
