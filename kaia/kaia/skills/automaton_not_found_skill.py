from typing import *
from kaia.avatar.dub.languages.en import *
from ..core import SingleLineKaiaSkill
from datetime import datetime

class AutomatonNotFoundReplies(TemplatesCollection):
    answer = Template(
        "Sorry, I don't understand."
    )


class AutomatonNotFoundSkill(SingleLineKaiaSkill):
    def __init__(self, datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        super().__init__(
            replies_class=AutomatonNotFoundReplies,
        )

    def run(self):
        input = yield
        if isinstance(input, Utterance) or isinstance(input, str):
            yield AutomatonNotFoundReplies.answer.utter()

