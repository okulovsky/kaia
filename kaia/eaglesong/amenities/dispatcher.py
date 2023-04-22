from typing import *
from kaia.eaglesong.core.subroutines import Routine, RoutineBase, Context, Return, Listen, Terminate
from kaia.eaglesong.core.interpreter import Automaton
from datetime import datetime
from dataclasses import dataclass

class SkillState:
    def __init__(self, context: Context, routine: RoutineBase):
        self.automaton = Automaton(routine, context)
        self.last_run = None #type: Optional[datetime]
        self.last_output = None #type: Any

    def expect(self, message):
        if self.last_run is None or self.last_output is None:
            return False
        if not isinstance(self.last_output, Listen):
            return False
        if self.last_output.expectation is None:
            return False
        return self.last_output.expectation.expect(message)




class Dispatcher(Routine):
    def __init__(self):
        self.skills = {} #type: Dict[str, RoutineBase]
        self.active_skills = {} #type: Dict[str, SkillState]

    def add_skill(self, name: str, skill):
        self.skills[name] = Routine.ensure(skill)

    def dispatch(self, context: Context):
        raise NotImplementedError()


    def should_listen(self, skill, output):
        return isinstance(output, Listen)

    def run(self, context: Context):
        while(True):
            skill_to_use = self.dispatch(context)
            if skill_to_use is not None:
                if skill_to_use not in self.active_skills:
                    if skill_to_use not in self.skills:
                        raise ValueError(f'Dispatcher returned {skill_to_use}, which is not found in skill list')
                    self.active_skills[skill_to_use] = SkillState(context, self.skills[skill_to_use])
                if skill_to_use not in self.active_skills:
                    raise ValueError(f'Skill was not found in active skills even after activation.')
                active_skill = self.active_skills[skill_to_use]
                active_skill.last_run = datetime.now()
                while True:
                    output = active_skill.automaton.process()
                    if isinstance(output,Return):
                        del self.active_skills[skill_to_use]
                        break
                    else:
                        active_skill.last_output = output
                        should_listen = self.should_listen(skill_to_use, output)
                        if should_listen:
                            break
                        else:
                            yield output
            yield Listen()








