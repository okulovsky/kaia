from ...framework import ISelfManagingDecider


class Mock(ISelfManagingDecider):
    def __init__(self, decider_name: str = "MockDecider"):
        self.decider_name = decider_name
        self.parameter = None

    def get_custom_decider_name(self) -> str:
        return self.decider_name

    def warmup(self, parameter: str|None):
        self.parameter = parameter

    def cooldown(self):
        self.parameter = None

