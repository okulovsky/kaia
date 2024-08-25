from typing import *
from kaia.dub.languages.en import *
from ..core import SingleLineKaiaSkill
from datetime import datetime
from kaia.narrator import World

class PingIntents(TemplatesCollection):
    question = Template(
        'Are you here?',
    )


class PingReplies(TemplatesCollection):
    answer = (
        Template("Sure, I'm listening.")
        .paraphrase(f"{World.user} asks if {World.character} is still listening to {World.user}, and {World.character} wants to confirm")
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

