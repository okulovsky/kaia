import copy
from unittest import TestCase
from ..interpreter import IAutomaton
from .helping_types import Stash, CheckType, CheckValue
from .testing_interpreter import DefaultFeedbackFactory, TestingInterpreter
from typing import *
import time
from dataclasses import dataclass
import inspect
from abc import ABC, abstractmethod

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


class IAsserter(ABC):
    @abstractmethod
    def assertion(self, actual, test_case: TestCase):
        pass



class Scenario:
    def __init__(self,
                 automaton_factory: Callable[[], IAutomaton],
                 printing = None,
                 feedback_factory = None,
                 keep_listens_type_in_log: Optional[Iterable[Type]] = None
                 ):
        self.automaton_factory = automaton_factory
        self.feedback_factory = DefaultFeedbackFactory() if feedback_factory is None else feedback_factory
        self.printing = Scenario.default_printing if printing is None else printing
        self.keep_listens_type = tuple(keep_listens_type_in_log) if keep_listens_type_in_log is not None else ()

        self.stages = []  # type: List[Stage]
        self.wait_on_next_stage = None
        self.act_on_next_stage = None

        self.stashed_values = {}
        self._forks: Dict[str,'Scenario'] = {}
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

    def fork(self, name: str) -> 'Scenario':
        self._forks[name] = copy.deepcopy(self)
        return self

    def get_fork(self, name: str) -> 'Scenario':
        return copy.deepcopy(self._forks[name])


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
            elif isinstance(checker, IAsserter):
                fixed_checkers.append(checker.assertion)
            else:
                fixed_checkers.append(CheckValue(checker))
        self.stages[-1].expectations = list(fixed_checkers)
        return self


    def _validate_stage(self, stage_index: int, s: Stage, response: List, test_case: TestCase) -> Tuple[Optional[Exception], Optional[str]]:
        if s.expectations is not None:
            if len(s.expectations) != len(response):
                return None, f"Error at stage#{stage_index}: wrong amount of output, expected {len(s.expectations)} but was {len(response)}"
            for j, q in enumerate(zip(s.expectations, response)):
                err_msg = f'Stage {stage_index}, expectation {j}\n> {s.prompt} \n< {q[1]}\nExpectation: {q[0]}\n\n'
                signature = inspect.signature(q[0])
                if len(signature.parameters) == 2:
                    try:
                        q[0](q[1], test_case)
                    except Exception as e:
                        return e, err_msg
                elif len(signature.parameters) == 1:
                    try:
                        result = q[0](q[1])
                        if not result:
                            return None, err_msg+f"Returned {result}"
                    except Exception as e:
                        return e, err_msg
        return None, None

    def validate(self, test_case: TestCase|None = None):
        if test_case is None:
            test_case = TestCase()

        aut = self.automaton_factory()
        interpreter = TestingInterpreter(aut, self.feedback_factory, self.keep_listens_type)
        self.log = []
        first_exception = None
        first_exception_base = None

        for i, s in enumerate(self.stages):
            if s.wait_before is not None:
                time.sleep(s.wait_before)
            if s.act_before is not None:
                s.act_before()

            try:
                interpreter.process(s.prompt)
            except Exception as ex:
                if self.printing is not None:
                    self.printing(self.log, True)
                raise ValueError(f"Error when processing input {s.prompt}") from ex


            base_exception, error_msg = self._validate_stage(i,s,interpreter.current_log, test_case)
            item = LogItem(s.label, s.prompt, interpreter.current_log)

            if error_msg is not None:
                exception = ValueError(error_msg)
                item.exception = exception
                item.exception_base = base_exception
                if first_exception is None:
                    first_exception = exception
                    first_exception_base = base_exception

            self.log.append(item)

        if self.printing is not None:
            self.printing(self.log, first_exception is not None)

        if first_exception is not None:
            if first_exception_base is not None:
                raise first_exception from first_exception_base
            else:
                raise first_exception

        return self


    @staticmethod
    def default_printing(log: List[LogItem], failure: bool = False):
        return Scenario.default_printing_generic(log, str, str, failure)

    @staticmethod
    def default_printing_generic(log: List[LogItem], prompt_to_str, response_to_str, failure: bool):
        if failure:
            print('\033[91mFAILURE\033[0m')
        else:
            print('\033[92mSUCCESS\033[0m')
        for index, item in enumerate(log):
            if item.label is not None:
                print('\033[92m'+item.label+'\033[0m')
            print('\033[94m' + str(index).ljust(3) + 'prompt'.ljust(10) + '\033[0m', prompt_to_str(item.prompt))
            for response in item.response:
                print('\033[94m' + 'response'.ljust(15) + '\033[0m', response_to_str(response))
            if item.exception is not None:
                print('\033[91m' + 'exception'.ljust(10) + '\033[0m', item.exception)
            if item.exception is not None:
                print('\033[91m' + 'exc_base'.ljust(10) + '\033[0m', item.exception_base)
        print('\n\n')
