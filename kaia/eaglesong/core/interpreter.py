import dataclasses
from typing import *
from types import GeneratorType
from abc import ABC, abstractmethod

class _NoAutomatonInput:
    pass

@dataclasses.dataclass
class _InterpreterInstruction:
    interrupt_cycle: bool
    reset_automaton: bool
    returned_value: Any

@dataclasses.dataclass
class InterpreterFilter:
    condition: Callable[[Any],bool]
    handler: Any

class IAutomaton(ABC):
    @abstractmethod
    def process(self, item: Any):
        pass


class Interpreter:
    def __init__(self,
                 automaton: IAutomaton,
                 ):
        self.automaton = automaton
        self.filters = [] #type: List[InterpreterFilter]

    @staticmethod
    def continue_cycle(value = None):
        return _InterpreterInstruction(False, False, value)

    @staticmethod
    def interrupt_cycle():
        return _InterpreterInstruction(True, False, None)

    @staticmethod
    def reset_automaton():
        return _InterpreterInstruction(True, True, None)

    def handle_type(self, type: Type, handler: Callable[[Any,Any], _InterpreterInstruction]):
        self.filters.append(InterpreterFilter(lambda z: isinstance(z, type), handler))

    def handle_type_async(self, type: Type, handler: Callable[[Any,Any], Awaitable[_InterpreterInstruction]]):
        self.filters.append(InterpreterFilter(lambda z: isinstance(z, type), handler))

    def _process_and_get_filter(self, item):
        response = self.automaton.process(item)
        filter = None  # type: Optional[InterpreterFilter]
        for candidate_filter in self.filters:
            if candidate_filter.condition(response):
                filter = candidate_filter
                break
        if filter is None:
            raise NotImplementedError(f'Missing handler for the response {type(response)} on the input {item}')
        return response, filter

    async def _async_process(self, item):
        automaton_input = item
        while True:
            response, filter = self._process_and_get_filter(automaton_input)
            instruction = await filter.handler(response)
            if instruction.reset_automaton:
                self.automaton = None
            if instruction.interrupt_cycle:
                break
            automaton_input = instruction.returned_value

    def _process(self, item):
        automaton_input = item
        while True:
            response, filter = self._process_and_get_filter(automaton_input)
            instruction = filter.handler(response)
            if instruction.reset_automaton:
                self.automaton = None
            if instruction.interrupt_cycle:
                break
            automaton_input = instruction.returned_value

    def has_exited(self):
        return self.automaton is None



