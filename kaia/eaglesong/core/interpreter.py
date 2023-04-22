import dataclasses
from typing import *
from .subroutines import RoutineBase, Context, Return
from types import GeneratorType

class _NoAutomatonInput:
    pass

@dataclasses.dataclass
class _InterpreterInstruction:
    interrupt_cycle: bool
    reset_automaton: bool

@dataclasses.dataclass
class _Filter:
    condition: Callable[[Any],bool]
    handler: Any

class Automaton:
    def __init__(self, subroutine: RoutineBase, context: Context):
        self.subroutine = RoutineBase.ensure(subroutine)
        self.context = context
        self.iterator = None
        
    def reset(self):
        self.iterator = self.subroutine.instantiate(self.context)
        if not isinstance(self.iterator, GeneratorType):
            raise ValueError(f'Probably forgotten `yield` in the function `{self.subroutine.get_name()}`')


    def notify(self, notification_source):
        if hasattr(self.subroutine, '_push_notification'):
            self.subroutine._push_notification(notification_source, self.context)

    def process(self):
        if self.iterator is None:
            self.reset()
        try:
            self.notify('automaton')
            return self.iterator.__next__()
        except StopIteration:
            self.iterator = None
            return Return()
        
    
class Interpreter:
    def __init__(self,
                 subroutine: RoutineBase,
                 context: Context,
                 is_async = False
                 ):
        self.automaton = Automaton(subroutine, context)
        self.filters = [] #type: List[_Filter]
        self.context = context

    @staticmethod
    def continue_cycle():
        return _InterpreterInstruction(False, False)

    @staticmethod
    def interrupt_cycle():
        return _InterpreterInstruction(True, False)

    @staticmethod
    def reset_automaton():
        return _InterpreterInstruction(True, True)

    def handle_type(self, type: Type, handler: Callable[[Any,Any], _InterpreterInstruction]):
        self.filters.append(_Filter(lambda z: isinstance(z, type), handler))

    def handle_type_async(self, type: Type, handler: Callable[[Any,Any], Awaitable[_InterpreterInstruction]]):
        self.filters.append(_Filter(lambda z: isinstance(z, type), handler))

    def _process_and_get_filter(self):
        response = self.automaton.process()
        filter = None  # type: Optional[_Filter]
        for candidate_filter in self.filters:
            if candidate_filter.condition(response):
                filter = candidate_filter
                break
        if filter is None:
            raise NotImplementedError(f'Missing handler for the response {response} on the input {self.context}')
        return response, filter

    async def _async_process(self):
        self.automaton.notify('interpreter')
        while True:
            response, filter = self._process_and_get_filter()
            instruction = await filter.handler(response)
            if instruction.reset_automaton:
                self.automaton = None
            if instruction.interrupt_cycle:
                break

    def _process(self):
        self.automaton.notify('interpreter')
        while True:
            response, filter = self._process_and_get_filter()
            instruction = filter.handler(response)
            if instruction.reset_automaton:
                self.automaton = None
            if instruction.interrupt_cycle:
                break

    def has_exited(self):
        return self.automaton is None



