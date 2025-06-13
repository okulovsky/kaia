from typing import *
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill
from datetime import datetime
from avatar import World

class PingIntents(TemplatesCollection):
    question = Template(
        'Are you here?',
    )


class PingReplies(TemplatesCollection):
    answer = (
        Template("Sure, I'm listening.")
        .context(
            f"{World.user} asks if {World.character} is still listening to {World.user}, and {World.character} confirms",
            reply_to=PingIntents.question
        )
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

