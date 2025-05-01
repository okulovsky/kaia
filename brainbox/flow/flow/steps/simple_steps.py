from .step import IStep


class ConstantStep(IStep):
    def __init__(self, records: list):
        self.records = records

    def process(self, history, current):
        return self.records


class FilterStep(IStep):
    def __init__(self, filter):
        self.filter = filter

    def process(self, history, current):
        return [o for o in current if self.filter(o)]

