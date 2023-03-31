from typing import *
from .subroutines import Subroutine, SubroutineBase
from .automaton import AbstractAutomaton, Return, Listen
from .pushdown_automaton import PushdownAutomaton

class InterruptionHandler:
    def __init__(self, accepts_check, subroutine: SubroutineBase):
        self.accepts_check = accepts_check
        self.subroutine = subroutine

class InterruptableAutomaton(AbstractAutomaton):
    def __init__(self, handlers: Iterable[InterruptionHandler], default: SubroutineBase):
        self.handlers = handlers
        self.current_handler = None #type: Optional[PushdownAutomaton]
        self.default = PushdownAutomaton(default)

    def process_hander(self, item):
        result = self.current_listener.process(item)
        if isinstance(result, Return):
            self.current_listener = None
            return Listen()
        return result

    def process(self, item):
        if self.current_handler is not None:
            return self.process_hander(item)

        for handler in self.handlers:
            if handler.accepts_check(item):
                 self.current_listener = PushdownAutomaton(handler.subroutine)
                 return self.process_hander(item)

        return self.default.process(item)







