from typing import *
from grammatron import *
from kaia import SingleLineKaiaSkill, World
from datetime import datetime
from .notification_skill import NotificationRegister, NotificationInfo


DURATION_INPUT = VariableDub(
    'duration',
    TimedeltaDub(True, True, False),
    'the duration of the timer'
)

DURATION_OUTPUT = VariableDub(
    'duration',
    TimedeltaDub(True, True, True),
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
    set_the_timer: ClassVar[Template] = Template(
        f'Set the timer for {DURATION_INPUT}',
    )
    cancel_the_timer:ClassVar[Template] = Template(
        'Cancel the timer',
        f'Cancel the {INDEX} timer',
    )
    how_much_timers: ClassVar[Template] = Template(
        'How much timers do I have?'
    )
    how_much_time_left: ClassVar[Template] = Template(
        "How much time left?"
    )


class TimerReplies(TemplatesCollection):
    timer_is_set: ClassVar[Template] = (
        Template(
            f'The timer for {DURATION_OUTPUT} is set',
            f'{INDEX} timer for {DURATION_OUTPUT} is set',
        ).context(
            f'{World.user} asks to set the timer, and {World.character} agrees'
        )
    )

    timer_is_cancelled: ClassVar[Template] = Template(
        'The timer is cancelled',
        f'The {INDEX} timer is cancelled',
    ).context(
        f'{World.user} asks to cancel the previously set the timer, and {World.character} agrees'
    )

    which_timer_error: ClassVar[Template] = Template(
        f'You have {AMOUNT} timers, I do not know which one to cancel.',
    ).context(
        reply_to=TimerIntents.cancel_the_timer,
        reply_details=f"{World.user} didn't specify the timer's index, but several timers are currently active"
    )

    no_such_timer: ClassVar[Template] = Template(
        f'I do not have the {INDEX} timer',
    ).context(
        reply_to=TimerIntents.cancel_the_timer,
        reply_details=f"{World.user} requested to cancel the specific timer, but this timer is not currently active"
    )

    no_timers: ClassVar[Template] = Template(
        'I do not have timers'
    ).context(
        reply_to=TimerIntents.how_much_timers,
        reply_details="No timers are available"
    )

    you_have: ClassVar[Template] = Template(
        f"You have {PluralAgreement(AMOUNT, 'timer')}",
    ).context(
        reply_to=TimerIntents.how_much_timers
    )

    timer_description: ClassVar[Template] = Template(
        f'The {INDEX} timer has {DURATION_OUTPUT}',
        f'The timer has {DURATION_OUTPUT}'
    ).context(
        f'{World.user} asks about the remaining time on the timer, and {World.character} replies'
    )


class TimerSkill(SingleLineKaiaSkill):
    def __init__(self,
                 register: Optional[NotificationRegister] = None,
                 datetime_factory: Callable[[], datetime] = datetime.now):
        self.datetime_factory = datetime_factory
        self.timers : List[NotificationInfo] = register.instances if register is not None else {}
        super().__init__(
            TimerIntents,
            TimerReplies,
        )

    def _set_timer(self, input: Utterance):
        duration = input.value['duration']
        timer_info = NotificationInfo(self.datetime_factory(), duration)
        self.timers.append(timer_info)
        if len(self.timers) == 1:
            yield TimerReplies.timer_is_set.utter(duration=duration)
        else:
            yield TimerReplies.timer_is_set.utter(duration=duration, index=len(self.timers))


    def _cancel_timer(self, input: Utterance):
        if len(self.timers) == 1:
            del self.timers[0]
            yield TimerReplies.timer_is_cancelled.utter()
            return
        elif len(self.timers) == 0:
            yield TimerReplies.no_timers()
            return

        if 'index' not in input.value:
            yield TimerReplies.which_timer_error.utter(amount=len(self.timers))
            return
        index = input.value['index'] - 1
        if index<0 or index>=len(self.timers):
            yield TimerReplies.no_such_timer.utter(index=index+1)

        del self.timers[index]
        yield TimerReplies.timer_is_cancelled.utter(index=index+1)


    def _get_remaining_time(self, index: int):
        info = self.timers[index]
        return info.duration - (self.datetime_factory() - info.start)


    def _describe_timers(self):
        utterances = [TimerReplies.you_have.utter(amount=len(self.timers))]
        for index, _ in enumerate(self.timers):
            utterances.append(TimerReplies.timer_description.utter(index=index+1, duration=self._get_remaining_time(index)))
        yield UtterancesSequence(*utterances)


    def run(self):
        input: Utterance = yield

        if input in TimerIntents.set_the_timer:
            yield from self._set_timer(input)
        elif input in TimerIntents.cancel_the_timer:
            yield from self._cancel_timer(input)
        elif input in TimerIntents.how_much_time_left:
            if len(self.timers) == 0:
                yield TimerReplies.no_timers()
            elif len(self.timers) == 1:
                yield TimerReplies.timer_description(duration = self._get_remaining_time(0))
            else:
                yield from self._describe_timers()
        elif input in TimerIntents.how_much_timers:
            yield from self._describe_timers()



















