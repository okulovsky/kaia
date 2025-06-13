from typing import *
from eaglesong.core import Return
from kaia.kaia import SingleLineKaiaSkill
from eaglesong.templates import *
from datetime import date, timedelta, datetime
from enum import Enum
from avatar import World

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

DELTA = TemplateVariable(
    "delta",
    description="The day relative to today, e.g. the word `yesterday` or `day after tomorrow`",
    dub = OptionsDub(RelativeDay)
)

DATE = TemplateVariable(
    "date",
    description="The full date of the day"
)

WEEKDAY = TemplateVariable(
    "weekday",
    description="The weekday, e.g. the word `Monday` or `Thursday`"
)


class DateIntents(TemplatesCollection):
    question = Template(
        f'What is the date?',
        f'What date is {DELTA}?',
        f'What date was {DELTA}?',
    )

class DateReplies(TemplatesCollection):
    answer = (
        Template(f"It is {WEEKDAY}, {DATE}.")
        .context(
            f"{World.user} asks what date is today, and {World.character} replies with an exact answer.",
            reply_to=DateIntents.question
        )
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

        if input not in DateIntents.question:
            raise Return()

        if 'delta' not in input.value:
            delta = 0
        else:
            delta = input.value['delta'].value

        date = self.datetime_factory() + timedelta(days=delta)
        if isinstance(date, datetime):
            date = date.date()

        yield DateReplies.answer.utter(
            WEEKDAY.assign(Weekdays(date.weekday())),
            DATE.assign(date)
        )







