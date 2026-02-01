from typing import *
from grammatron import *
from kaia import SingleLineKaiaSkill, World
from datetime import datetime

class PingIntents(TemplatesCollection):
    question: ClassVar[Template] = Template(
        'Are you here?',
    )


class PingReplies(TemplatesCollection):
    answer: ClassVar[Template] = (
        Template("Sure, I'm listening.")
        .context(
            f"{World.user} asks if {World.character} is still listening to {World.user}, and {World.character} confirms",
            reply_to=PingIntents.question
        )
    )

class PingSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(
            PingIntents,
            PingReplies,
        )

    def run(self):
        yield PingReplies.answer.utter()

