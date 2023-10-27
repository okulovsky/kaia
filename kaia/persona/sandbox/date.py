from ...eaglesong.core import Return
from ..dialogue import AssistantSkill
from ..dub.languages.en import *
from .common_replies import CommonReplies
from datetime import date, timedelta
from enum import Enum

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
    answer = Template(
        "It is {weekday}, {date}.",
        weekday = EnumDub(Weekdays),
        date = DateDub()
    )


class DateSkill(AssistantSkill):
    def __init__(self, datetime_factory: Callable[[], date] = date.today):
        self.datetime_factory = datetime_factory
        super().__init__(
            self.run,
            DateIntents,
            DateReplies,
            [DateIntents.question],
            {'/date': DateIntents.question.utter()},
        )

    def run(self):
        input = yield #type: Utterance

        if input.template.name!=DateIntents.question.name:
            yield CommonReplies.wrong_state.utter()
            raise Return()

        if 'delta' not in input.value:
            delta = 0
        else:
            delta = input.value['delta'].value

        date = self.datetime_factory() + timedelta(days=delta)

        yield DateReplies.answer.utter(
            weekday = Weekdays(date.weekday()),
            date = date
        )







