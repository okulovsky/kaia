from typing import *
from kaia.dub.languages.en import *
from ..core import SingleLineKaiaSkill
from datetime import datetime

class ExceptionInSkillReplies(TemplatesCollection):
    answer = Template(
        "Exception has occured. The skill was interrupted, but assistant runs normally"
    )


class ExceptionHandledSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(
            replies_class=ExceptionInSkillReplies,
        )

    def run(self):
        yield ExceptionInSkillReplies.answer.utter()

