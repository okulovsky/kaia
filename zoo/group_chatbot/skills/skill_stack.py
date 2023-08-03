from typing import *
from kaia.eaglesong.core import Return, RoutineBase, Automaton, Routine, PushdownFilter


class SkillStack(Routine):
    def __init__(self,
                 skills: List[RoutineBase]
                 ):
        self.skills = skills

    def run(self, context):
        input = context.get_input()
        for skill in self.skills:
            context.set_input(input)
            aut = Automaton(RoutineBase.interpretable(skill, PushdownFilter), context)
            handled = False
            while True:
                result = aut.process()
                if isinstance(result, Return):
                    break
                handled = True
                yield result
            if handled:
                break
        yield Return()