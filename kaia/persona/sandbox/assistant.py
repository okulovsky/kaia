from typing import *
from ..dialogue import Assistant, IAssistantSkill
from .common_replies import CommonReplies

class HomeAssistant(Assistant):
    def __init__(self, skills: Iterable[IAssistantSkill]):
        super().__init__(
            skills,
            CommonReplies,
            self.not_found
        )

    def not_found(self):
        yield CommonReplies.not_recognized.utter()

