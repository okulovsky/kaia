from eaglesong.core import Return
from typing import *
from grammatron import *
from kaia import SingleLineKaiaSkill, World
from datetime import datetime
from .notification_skill import NotificationRegister, NotificationInfo



DURATION = VariableDub(
    'duration',
    TimedeltaDub(0,2),
    'the duration of the timer'
)

INDEX = VariableDub(
    'index',
    OrdinalDub(1,10),
    'when several timers are used, the index of the timer, so `first`, `second`, etc up to `tenth`.'
)

AMOUNT = VariableDub(
    'amount',
    CardinalDub(1,10),
    "the amount of currently active timers"
)

class TimerIntents(TemplatesCollection):
    set_the_timer = Template(
        f'Set the timer for {DURATION}',
        f'Set the {INDEX} timer for {DURATION}',
    )
    cancel_the_timer = Template(
        'Cancel the timer',
        f'Cancel the {INDEX} timer',
    )
    how_much_timers = Template(
        'How much timers do I have?'
    )


class TimerReplies(TemplatesCollection):
    timer_is_set = (
        Template(
            f'The timer for {DURATION} is set',
            f'{INDEX} timer for {DURATION} is set',
        ).context(
            f'{World.user} asks to set the timer, and {World.character} agrees'
        )
    )

    timer_is_cancelled = Template(
        'The timer is cancelled',
        f'The {INDEX} timer is cancelled',
    ).context(
        f'{World.user} asks to cancel the previously set the timer, and {World.character} agrees'
    )

    which_timer_error = Template(
        f'You have {AMOUNT} timers, I do not know which one to cancel.',
    ).context(
        reply_to=TimerIntents.cancel_the_timer,
        reply_details=f"{World.user} didn't specify the timer's index, but several timers are currently active"
    )

    no_such_timer = Template(
        f'I do not have the {INDEX} timer',
    ).context(
        reply_to=TimerIntents.cancel_the_timer,
        reply_details=f"{World.user} requested to cancel the specific timer, but this timer is not currently active"
    )

    no_timers = Template(
        'I do not have timers'
    ).context(
        reply_to=TimerIntents.how_much_timers,
        reply_details="No timers are available"
    )

    you_have = Template(
        f"You have {PluralAgreement(AMOUNT, 'timer')}",
    ).context(
        reply_to=TimerIntents.how_much_timers
    )

    timer_description = Template(
        f'The {INDEX} timer has {DURATION}',
    ).context(
        f'{World.user} asks about the remaining time on the timer, and {World.character} replies'
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

        if input in TimerIntents.set_the_timer:
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

        if input in TimerIntents.cancel_the_timer:
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

        if input in TimerIntents.how_much_timers:
            if len(self.timers) == 0:
                yield TimerReplies.no_timers.utter()
            else:
                utterances = [TimerReplies.you_have.utter(amount=len(self.timers))]
                for index in sorted(self.timers):
                    info = self.timers[index]
                    utterances.append(TimerReplies.timer_description.utter(index=index, duration = info.duration - (self.datetime_factory() - info.start)))
                yield UtterancesSequence(*utterances)















