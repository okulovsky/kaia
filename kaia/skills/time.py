from typing import *
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill
from datetime import datetime
from avatar import World

class TimeIntents(TemplatesCollection):
    question = Template(
        'What time is it?',
        'What is the time?'
    )

HOURS = TemplateVariable('hours')
MINUTES = TemplateVariable('minutes')

class TimeReplies(TemplatesCollection):
    answer = (
        Template(f'It is {HOURS} {PluralAgreement("hours").as_variable()} and {MINUTES} {PluralAgreement("minutes").as_variable()}.')
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

