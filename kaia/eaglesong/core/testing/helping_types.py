class CheckType:
    def __init__(self, type):
        self.type = type

    def __call__(self, v):
        if not isinstance(v, self.type):
            raise ValueError(f"Value {v} is expected to be of type {self.type}, but was `{v}`")
        return True


class CheckValue:
    def __init__(self, expected):
        self.expected = expected

    def __call__(self, v):
        if v != self.expected:
            raise ValueError(f"Expected `{self.expected}` but was `{v}`")
        return True


class Stash:
    def __init__(self, slot):
        self.slot = slot
        self.scenario = None

    def __call__(self, v):
        self.scenario.stashed_values[self.slot] = v
        return True