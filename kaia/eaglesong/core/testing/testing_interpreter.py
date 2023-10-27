from typing import *
from ..interpreter import Interpreter, InterpreterFilter, IAutomaton
from ..primitives import Return, Terminate, Listen


class DefaultFeedbackFactory:
    def __init__(self):
        self.current_id = 0

    def __call__(self, response):
        self.current_id+=1
        return self.current_id

class TestingInterpreter(Interpreter):
    def __init__(self,
                 automaton: IAutomaton,
                 feedback_factory: Callable[[Any], Any]
                 ):
        super(TestingInterpreter, self).__init__(automaton)
        self.filters.append(InterpreterFilter(lambda _: True, self.handle_everything))
        self.current_log = []
        self.feedback_factory = feedback_factory

    def handle_everything(self, response):
        if not isinstance(response, Listen):
            self.current_log.append(response)
        if isinstance(response, Return) or isinstance(response, Terminate) or isinstance(response, Listen):
            return Interpreter.interrupt_cycle()
        feedback = self.feedback_factory(response)
        return Interpreter.continue_cycle(feedback)

    def process(self, item):
        self.current_log = []
        self._process(item)