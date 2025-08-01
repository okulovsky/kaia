from typing import *
from grammatron import *
from kaia import SingleLineKaiaSkill, World
from datetime import datetime

class TimeIntents(TemplatesCollection):
    question = Template(
        'What time is it?',
        'What is the time?'
    )

HOURS = VariableDub('hours')
MINUTES = VariableDub('minutes')

class TimeReplies(TemplatesCollection):
    answer = (
        Template(f'It is {PluralAgreement(HOURS, "hour")} and {PluralAgreement(MINUTES, "minute")}.')
        .no_paraphrasing()
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
        reply = TimeReplies.answer.utter(hours = time.hour, minutes = time.minute)
        yield reply

