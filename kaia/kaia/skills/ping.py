from typing import *
from kaia.avatar.dub.languages.en import *
from ..core import SingleLineKaiaSkill
from datetime import datetime

class PingIntents(TemplatesCollection):
    question = Template(
        'Are you here?',
    )


class PingReplies(TemplatesCollection):
    answer = Template(
        "Sure, I'm listening."
    )

class PingSkill(SingleLineKaiaSkill):
    def __init__(self, datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        super().__init__(
            PingIntents,
            PingReplies,
        )

    def run(self):
        yield PingReplies.answer.utter()

