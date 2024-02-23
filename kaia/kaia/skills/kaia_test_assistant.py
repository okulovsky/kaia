from typing import *
from ..core import KaiaAssistant, SingleLineKaiaSkill
from .automaton_not_found_skill import AutomatonNotFoundSkill
from .exception_in_skill import ExceptionHandledSkill

class KaiaTestAssistant(KaiaAssistant):
    def __init__(self,
                 skills: List[SingleLineKaiaSkill],
                 initialization: Optional[Callable] = None
                 ):
        super().__init__(
            skills,
            AutomatonNotFoundSkill(),
            exception_in_skill=ExceptionHandledSkill(),
            initialization = initialization
        )
