from typing import *
from .subroutines import SubroutineBase

class Return:
    def __init__(self, *return_value):
        if len(return_value) == 0:
            self.return_value = None
        elif len(return_value) == 1:
            self.return_value = return_value[0]
        else:
            self.return_value = return_value


class Terminate:
    def __init__(self, message: str):
        self.message = message


class Listen:
    pass


class AbstractAutomaton:
    def process(self, item):
        raise NotImplementedError()


class Automaton(AbstractAutomaton):
    def __init__(self, subroutine: SubroutineBase):
        self.subroutine = subroutine
        self.reset()

    def reset(self):
        self.iterator = iter(self.subroutine.instantiate(self.get_current))

    def get_current(self):
        return self.current

    def process(self, item):
        self.current = item
        try:
            return self.iterator.__next__()
        except StopIteration:
            return Return()
