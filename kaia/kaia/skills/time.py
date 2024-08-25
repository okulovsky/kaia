from typing import *
from kaia.dub.languages.en import *
from ..core import SingleLineKaiaSkill
from datetime import datetime
from kaia.narrator import World

class TimeIntents(TemplatesCollection):
    question = Template(
        'What time is it?',
        'What is the time?'
    )


class TimeReplies(TemplatesCollection):
    answer = (
        Template(
        'It is {hours} {hours_word} and {minutes} {minutes_word}.',
        hours = CardinalDub(0, 24),
        hours_word = PluralAgreement('hours', 'hour', 'hours'),
        minutes = CardinalDub(0, 60),
        minutes_word = PluralAgreement('minutes', 'minute', 'minutes'))
        .paraphrase.after(f'{World.user} asks {World.character} what time is it, and {World.character} provides an exact and correct answer.')
    )

class TimeSkill(SingleLineKaiaSkill):
    def __init__(self, datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        super().__init__(
            TimeIntents,
            TimeReplies,
        )

    def run(self):
        time = self.datetime_factory()
        yield TimeReplies.answer.utter(hours = time.hour, minutes = time.minute)

