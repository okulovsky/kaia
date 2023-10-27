from typing import *
from kaia.eaglesong.core import Return, Automaton, ContextRequest


class SkillStack:
    def __init__(self,
                 skills: List[Callable]
                 ):
        self.skills = skills

    def __call__(self):
        main_input = yield None
        context = yield ContextRequest()

        for skill in self.skills:
            input = main_input
            aut = Automaton(skill, context)
            handled = False
            while True:
                result = aut.process(input)
                if isinstance(result, Return):
                    break
                handled = True
                input = yield result
            if handled:
                break
