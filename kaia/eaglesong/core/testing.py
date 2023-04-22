from typing import *
from .interpreter import Automaton, RoutineBase
from .subroutines import Listen, Return, Terminate, Context, PushdownFilter
import time
from yo_fluq_ds import Obj

class Stage:
    def __init__(self, prompt, wait_before: Optional[float], label: Optional[str]):
        self.wait_before = wait_before
        self.prompt = prompt
        self.label = label
        self.expectations = None #type: Optional[List[Callable]]


class Scenario:
    def __init__(self,
                 context_factory: Callable[[], Context],
                 routine: RoutineBase,
                 filters=None,
                 printing = print,
                 feedback_input_factory = None
                 ):
        self.context_factory = context_factory
        self.routine = routine
        self.feedback_input_factory = feedback_input_factory

        self.filters = filters if filters is not None else (PushdownFilter,)
        self.printing = printing

        self.stages = []  # type: List[Stage]
        self.wait_on_next_stage = None

        self.stashed_values = {}
        self.log = []

    def send(self, obj, label = None) -> 'Scenario':
        self.stages.append(Stage(obj, self.wait_on_next_stage, label))
        self.wait_on_next_stage = None
        return self

    def wait(self, value) ->'Scenario':
        self.wait_on_next_stage = value
        return self


    def check(self, *checkers):
        fixed_checkers = []
        for checker in checkers:
            if isinstance(checker, type):
                fixed_checkers.append(Scenario._check_type(checker))
            elif isinstance(checker, Scenario.stash):
                checker.scenario = self
                fixed_checkers.append(checker)
            elif callable(checker):
                fixed_checkers.append(checker)
            else:
                fixed_checkers.append(Scenario._check_value(checker))
        self.stages[-1].expectations = list(fixed_checkers)
        return self

    class _check_type:
        def __init__(self, type):
            self.type = type
        def __call__(self, v):
            if not isinstance(v, self.type):
                raise ValueError(f"Value {v} is not of type {self.type}")
            return True

    class _check_value:
        def __init__(self, expected):
            self.expected = expected
        def __call__(self, v):
            if v!=self.expected:
                raise ValueError(f"Expected {self.expected} but was {v}")
            return True

    class stash:
        def __init__(self, slot):
            self.slot = slot
            self.scenario = None

        def __call__(self, v):
            self.scenario.stashed_values[self.slot] = v
            return True


    def preview(self):
        return self.validate(ignore_errors=True)

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


    def validate(self, ignore_errors = False):
        context = self.context_factory()
        aut = Automaton(RoutineBase.interpretable(self.routine, *self.filters), context)
        log = []
        feedback = 0
        for i, s in enumerate(self.stages):
            if s.wait_before is not None:
                time.sleep(s.wait_before)
            response = []
            context.set_input(s.prompt)
            while True:
                c = aut.process()
                if isinstance(c, Listen):
                    break
                response.append(c)
                feedback+=1
                if self.feedback_input_factory is None:
                    feedback_input = feedback
                else:
                    feedback_input = self.feedback_input_factory(feedback)
                context.set_input(feedback_input)
                if isinstance(c, Return) or isinstance(c, Terminate):
                    break
            err = self._validate_stage(i,s,response)

            item = Obj()
            if s.label is not None:
                item['label'] = s.label
            item['prompt'] = s.prompt
            item['response'] = response

            if err is not None:
                base, ex = err
                if not ignore_errors:
                    if base is None:
                        raise ex
                    else:
                        raise ex from base
                else:
                    item['exception'] = ex
                    item['exception_base'] = base

            log.append(item)

        if self.printing is not None:
            self.printing(log)
        return self

    @staticmethod
    def default_printing(log):
        for item in log:
            for key, value in item.items():
                print('\033[94m' + key.ljust(10) + '\033[0m', value)
            print()