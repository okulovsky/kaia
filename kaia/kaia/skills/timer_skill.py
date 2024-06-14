from kaia.eaglesong.core import Return
from typing import *
from kaia.avatar.dub.languages.en import *
from kaia.kaia.core import SingleLineKaiaSkill
from datetime import datetime
from kaia.kaia.skills.notification_skill import NotificationRegister, NotificationInfo


class TimerIntents(TemplatesCollection):
    set_the_timer = Template(
        'Set the timer for {duration}',
        'Set the {index} timer for {duration}',
        duration = TimedeltaDub(),
        index = OrdinalDub(1,10)
    )
    cancel_the_timer = Template(
        'Cancel the timer',
        'Cancel the {index} timer',
        index = OrdinalDub(1, 10)
    )
    how_much_timers = Template(
        'How much timers do I have?'
    )


class TimerReplies(TemplatesCollection):
    timer_is_set = Template(
        'The timer for {duration} is set',
        '{index} timer for {duration} is set',
        duration = TimedeltaDub(),
        index = OrdinalDub(1, 10)
    )
    timer_is_cancelled = Template(
        'The timer is cancelled',
        'The {index} timer is cancelled',
        index = OrdinalDub(1, 10)
    )
    which_timer_error = Template(
        'You have {amount} timers, I do not know which one to cancel.',
        amount = CardinalDub(1, 10)
    )
    no_such_timer = Template(
        'I do not have the {index} timer',
        index = OrdinalDub(1, 10)
    )
    no_timers = Template(
        'I do not have timers'
    )
    you_have = Template(
        "You have {amount} {timers}",
        amount = CardinalDub(1, 10),
        timers = PluralAgreement('amount','timer','timers')
    )
    timer_description = Template(
        'The {index} timer has {remaining_time}',
        index = OrdinalDub(1, 10),
        remaining_time = TimedeltaDub()
    )


class TimerSkill(SingleLineKaiaSkill):
    def __init__(self,
                 register: Optional[NotificationRegister] = None,
                 datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        self.timers : Dict[str, NotificationInfo] = register.instances if register is not None else {}
        super().__init__(
            TimerIntents,
            TimerReplies,
        )

    def run(self):
        input: Utterance = yield

        if input.template.name == TimerIntents.set_the_timer.name:
            duration = input.value['duration']
            timer_info = NotificationInfo(self.datetime_factory(), duration)
            if 'index' in input.value:
                index = input.value['index']
            elif len(self.timers):
                index = max(self.timers) + 1
            else:
                index = 1
            self.timers[index] = timer_info
            if index == 1:
                yield TimerReplies.timer_is_set.utter(duration=duration)
            else:
                yield TimerReplies.timer_is_set.utter(duration=duration, index = index)

        if input.template.name == TimerIntents.cancel_the_timer.name:
            if 'index' in input.value:
                index = input.value['index']
            else:
                if len(self.timers) == 1:
                    index = max(self.timers)
                else:
                    yield TimerReplies.which_timer_error.utter(amount=len(self.timers))
                    raise Return()
            if index not in self.timers:
                if len(self.timers) != 0:
                    yield TimerReplies.no_such_timer.utter(index=index)
                else:
                    yield TimerReplies.no_timers.utter()
            del self.timers[index]
            if len(self.timers) == 0:
                yield TimerReplies.timer_is_cancelled.utter()
            else:
                yield TimerReplies.timer_is_cancelled.utter(index = index)

        if input.template.name == TimerIntents.how_much_timers.name:
            if len(self.timers) == 0:
                yield TimerReplies.no_timers.utter()
            else:
                yield TimerReplies.you_have.utter(amount=len(self.timers))
                for index in sorted(self.timers):
                    info = self.timers[index]
                    yield TimerReplies.timer_description.utter(index=index, remaining_time = info.duration - (self.datetime_factory() - info.start))















