from ..dub.languages.en import *
from ..dialogue import AssistantSkill
from datetime import datetime

class TimeIntents(TemplatesCollection):
    question = Template(
        'What time is it?',
        'What is the time?'
    )


class TimeReplies(TemplatesCollection):
    answer = Template(
        'It is {hours} {hours_word} and {minutes} {minutes_word}.',
        hours = CardinalDub(0, 24),
        hours_word = PluralAgreement('hours', 'hour', 'hours'),
        minutes = CardinalDub(0, 60),
        minutes_word = PluralAgreement('minutes', 'minute', 'minutes')
    )

class TimeSkill(AssistantSkill):
    def __init__(self, datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        super().__init__(
            self.run,
            TimeIntents,
            TimeReplies,
            [TimeIntents.question],
            {'/time': TimeIntents.question.utter()},
        )

    def run(self):
        time = self.datetime_factory()
        yield TimeReplies.answer.utter(hours = time.hour, minutes = time.minute)

