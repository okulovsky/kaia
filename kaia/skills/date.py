from typing import *
from eaglesong.core import Return
from kaia.kaia import SingleLineKaiaSkill
from kaia.dub.languages.en import *
from datetime import date, timedelta, datetime
from enum import Enum
from kaia.avatar import World

class RelativeDay(Enum):
    Today = 0
    Tomorrow = 1
    Yesterday = -1
    The_day_after_tomorrow = 2
    The_day_before_yesterday = -2


class Weekdays(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class DateIntents(TemplatesCollection):
    question = Template(
        'What is the date?',
        'What date is {delta}?',
        'What date was {delta}?',
        delta=EnumDub(RelativeDay)
    )

class DateReplies(TemplatesCollection):
    answer = (
        Template(
            "It is {weekday}, {date}.",
            weekday = EnumDub(Weekdays),
            date = DateDub())
        .paraphrase.after(f"{World.user} asks what date is today, and {World.character} replies with an exact answer.")
    )



class DateSkill(SingleLineKaiaSkill):
    def __init__(self, datetime_factory: Callable[[], date] = date.today):
        self.datetime_factory = datetime_factory
        super().__init__(
            DateIntents,
            DateReplies,
        )

    def run(self):
        input = yield #type: Utterance

        if input.template.name!=DateIntents.question.name:
            raise Return()

        if 'delta' not in input.value:
            delta = 0
        else:
            delta = input.value['delta'].value

        date = self.datetime_factory() + timedelta(days=delta)
        if isinstance(date, datetime):
            date = date.date()

        yield DateReplies.answer.utter(
            weekday = Weekdays(date.weekday()),
            date = date
        )







