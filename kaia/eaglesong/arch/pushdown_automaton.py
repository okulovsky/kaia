from typing import *
from .automaton import AbstractAutomaton, Automaton, Return
from .subroutines import SubroutineBase


class PushdownAutomatonNotification:
    def __init__(self, kind, name, item):
        self.kind=kind
        self.name=name
        self.item=item


class PushdownAutomaton(AbstractAutomaton):
    def __init__(self, subroutine: SubroutineBase, jump_call_back=None):
        self.subroutine = subroutine
        self.name = subroutine.get_name()
        self.stack = None #type: Optional[List[Automaton]]
        self.jump_call_back = jump_call_back

    def reset(self, item):
        self.stack = []
        self.push(self.subroutine, item)

    def push(self, subroutine: SubroutineBase, item):
        automaton = Automaton(subroutine)
        self.stack.append(automaton)
        if self.jump_call_back is not None:
            self.jump_call_back(PushdownAutomatonNotification('into', subroutine.get_name(), item))

    def pop(self, item, return_obj: Return):
        current = self.stack.pop()
        current.subroutine.return_value = return_obj.return_value

        if self.jump_call_back is not None:
            self.jump_call_back(PushdownAutomatonNotification('from', current.subroutine.get_name(), item))
            if len(self.stack)!=0:
                self.jump_call_back(PushdownAutomatonNotification('return', self.stack[len(self.stack)-1].subroutine.get_name(), item=item))

    def process(self, item):
        if self.stack is None:
            self.reset(item)

        while True:
            if len(self.stack) == 0:
                return Return()
            last = self.stack[len(self.stack)-1]
            result = last.process(item)
            if isinstance(result, Return):
                self.pop(item, result)
                continue
            elif isinstance(result,SubroutineBase):
                self.push(result, item)
                continue
            else:
                return result