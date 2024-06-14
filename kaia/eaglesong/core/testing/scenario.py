from ..interpreter import IAutomaton
from .helping_types import Stash, CheckType, CheckValue
from .testing_interpreter import DefaultFeedbackFactory, TestingInterpreter
from typing import *
import time
from dataclasses import dataclass

class Stage:
    def __init__(self, prompt, wait_before: Optional[float], label: Optional[str], act_before: Optional[Callable]):
        self.wait_before = wait_before
        self.prompt = prompt
        self.label = label
        self.expectations = None #type: Optional[List[Callable]]
        self.act_before = act_before

@dataclass
class LogItem:
    label: Optional[str]
    prompt: Any
    response: Any
    exception: Any = None
    exception_base: Any = None



class Scenario:
    def __init__(self,
                 automaton_factory: Callable[[], IAutomaton],
                 printing = None,
                 feedback_factory = None
                 ):
        self.automaton_factory = automaton_factory
        self.feedback_factory = DefaultFeedbackFactory() if feedback_factory is None else feedback_factory
        self.printing = Scenario.default_printing if printing is None else printing

        self.stages = []  # type: List[Stage]
        self.wait_on_next_stage = None
        self.act_on_next_stage = None

        self.stashed_values = {}
        self.log = [] #type: List[LogItem]

    def send(self, obj, label = None) -> 'Scenario':
        self.stages.append(Stage(obj, self.wait_on_next_stage, label, self.act_on_next_stage))
        self.wait_on_next_stage = None
        self.act_on_next_stage = None
        return self

    def wait(self, value) ->'Scenario':
        self.wait_on_next_stage = value
        return self

    def act(self, callable: Callable) -> 'Scenario':
        self.act_on_next_stage = callable
        return self

    @staticmethod
    def stash(slot):
        return Stash(slot)

    def check(self, *checkers):
        fixed_checkers = []
        for checker in checkers:
            if isinstance(checker, type):
                fixed_checkers.append(CheckType(checker))
            elif isinstance(checker, Stash):
                checker.scenario = self
                fixed_checkers.append(checker)
            elif callable(checker):
                fixed_checkers.append(checker)
            else:
                fixed_checkers.append(CheckValue(checker))
        self.stages[-1].expectations = list(fixed_checkers)
        return self


    def _validate_stage(self, stage_index: int, s: Stage, response: List):
        if s.expectations is not None:
            if len(s.expectations) != len(response):
                return None, ValueError(f"Error at stage#{stage_index}: wrong amount of output, expected {len(s.expectations)} but was {len(response)}")
            for j, q in enumerate(zip(s.expectations, response)):
                catched = False
                result = False
                err_msg = f'Stage {stage_index}, expectation {j}\n> {s.prompt} \n< {q[1]}\nExpectation: {q[0]}\n\n'
                try:
                    result = q[0](q[1])
                except Exception as e:
                    catched = True
                    return e, ValueError(err_msg)
                if not catched and not result:
                    return None, ValueError(err_msg)

    def validate(self):
        aut = self.automaton_factory()
        interpreter = TestingInterpreter(aut, self.feedback_factory)
        self.log = []
        first_exception = None
        first_exception_base = None

        for i, s in enumerate(self.stages):
            if s.wait_before is not None:
                time.sleep(s.wait_before)
            if s.act_before is not None:
                s.act_before()

            interpreter.process(s.prompt)
            err = self._validate_stage(i,s,interpreter.current_log)
            item = LogItem(s.label, s.prompt, interpreter.current_log)

            if err is not None:
                base, ex = err
                item.exception = ex
                item.exception_base = base
                if first_exception is None:
                    first_exception = ex
                    first_exception_base = base

            self.log.append(item)

        if self.printing is not None:
            self.printing(self.log)

        if first_exception is not None:
            if first_exception_base is not None:
                raise first_exception from first_exception_base
            else:
                raise first_exception

        return self


    @staticmethod
    def default_printing(log: List[LogItem]):
        return Scenario.default_printing_generic(log, str, str)

    @staticmethod
    def default_printing_generic(log: List[LogItem], prompt_to_str, response_to_str):
        for item in log:
            if item.label is not None:
                print('\033[92m'+item.label+'\033[0m')
            print('\033[94m' + 'prompt'.ljust(10) + '\033[0m', prompt_to_str(item.prompt))
            for response in item.response:
                print('\033[94m' + 'response'.ljust(15) + '\033[0m', response_to_str(response))
            if item.exception is not None:
                print('\033[91m' + 'exception'.ljust(10) + '\033[0m', item.exception)
            if item.exception is not None:
                print('\033[91m' + 'exc_base'.ljust(10) + '\033[0m', item.exception_base)
