from typing import *
from .assistant_skill import IAssistantSkill
from ...eaglesong.core import Automaton, ContextRequest, AutomatonExit, Listen
from ..dub.core import TemplatesCollection


class Assistant:
    def __init__(self,
                 skills: Iterable[IAssistantSkill],
                 common_replies: Type[TemplatesCollection],
                 skill_not_found: Callable
                 ):
        self.skills = tuple(skills)
        self.common_replies = common_replies
        self.mapping = {key: value for skill in skills for key, value in skill.get_shortcuts().items()}
        self.skill_not_found = skill_not_found


    def get_replies(self, include_intents = False):
        templates = self.common_replies.get_templates()
        for skill in self.skills:
            templates.extend(skill.get_replies())
            if include_intents:
                for intent in skill.get_intents():
                    templates.append(intent)
        return templates

    def get_intents(self):
        return [i for skill in self.skills for i in skill.get_intents()]


    def __call__(self):
        while True:
            input = yield
            if input in self.mapping:
                input = self.mapping[input]

            context = yield ContextRequest()
            aut = None #type: Optional[Automaton]
            for skill in self.skills:
                if not skill.should_run_on_input(input):
                    continue

                aut = Automaton(skill.get_runner(), context)
                break

            if aut is not None:
                while True:
                    reply = aut.process(input)
                    if isinstance(reply, AutomatonExit):
                        break
                    input = yield reply
            else:
                yield from self.skill_not_found()

            yield Listen()








