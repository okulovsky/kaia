from typing import *
from ..arch import PushdownAutomaton, FunctionalSubroutine, Listen, Return, Terminate
import telegram as tg
from datetime import datetime

class Stage:
    def __init__(self, prompt):
        self.prompt = prompt
        self.expectations = None #type: Optional[List[Callable]]

class Scenario:
    def __init__(self):
        self.stages = [] #type: List[Stage]

    def send(self, obj) -> 'Scenario':
        self.stages.append(Stage(obj))
        return self

    def check(self, *checkers):
        self.stages[-1].expectations = list(checkers)
        return self

    def validate(self, routine, ignore_errors = False):
        aut = PushdownAutomaton(FunctionalSubroutine.ensure(routine))
        log = []
        for i, s in enumerate(self.stages):
            response = []
            while True:
                c = aut.process(s.prompt)
                if isinstance(c, Listen):
                    break
                response.append(c)
                if isinstance(c, Return) or isinstance(c, Terminate):
                    break
            if s.expectations is not None:
                if len(s.expectations) != len(response):
                    raise ValueError(f"Error at stage#{i}: wrong amount of output, expected {len(s.expectations)} but was {len(response)}")
                for j, q in enumerate(zip(s.expectations, response)):
                    if not q[0](q[1]):
                        raise ValueError(f'Error at stage {i} at response {j}: expectation failed')
            log.append(dict(prompt=s.prompt, response=response))
        return log


