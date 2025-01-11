from unittest import TestCase
from datetime import datetime, timedelta
from eaglesong.core import Automaton, Scenario
from kaia.skills.timer_skill import TimerSkill, TimerReplies, TimerIntents
from kaia.skills.notification_skill import NotificationSkill, NotificationRegister
from kaia.kaia import DateTimeTestFactory, KaiaAssistant, TimerTick


def _factory(dtf, beautification):
    register = NotificationRegister('Alarm', 'Alarm cancelled' if beautification else None)
    notification = NotificationSkill([register], dtf, 10 if beautification else None)
    timer = TimerSkill(register, dtf)
    return Automaton(KaiaAssistant([timer, notification]), None)

def S(dtf: DateTimeTestFactory, with_after_audio = False):
    return Scenario(automaton_factory=lambda: _factory(dtf, with_after_audio))


class TestDate(TestCase):
    def test_timer_create(self):
        dtf = DateTimeTestFactory()
        (
            S(dtf)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=5)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=5)),
            )
            .send(TimerIntents.how_much_timers.utter())
            .check(
                TimerReplies.you_have.utter(amount=1) + TimerReplies.timer_description.utter(index=1, remaining_time = timedelta(minutes=5)),
            )
            .act(lambda: dtf.add(30))
            .send(TimerIntents.how_much_timers.utter())
            .check(
                TimerReplies.you_have(amount=1) + TimerReplies.timer_description(index=1, remaining_time=timedelta(minutes=4, seconds=30)),
            )
            .send(TimerIntents.cancel_the_timer.utter())
            .check(
                TimerReplies.timer_is_cancelled.utter(),
            )
            .validate()
        )

    def test_timer_works(self):
        dtf = DateTimeTestFactory()
        (
            S(dtf)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=5)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=5)),
            )
            .act(lambda: dtf.add(4*60+59))
            .send(TimerTick())
            .check()
            .act(lambda: dtf.add(1))
            .send(TimerTick())
            .check("Alarm")
            .send(TimerTick())
            .check("Alarm")
            .send("Stop")
            .check()
            .send(TimerTick())
            .check()
            .validate()
        )

    def test_timer_beautification(self):
        dtf = DateTimeTestFactory()
        (
            S(dtf, True)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=1)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=1)),
            )
            .act(lambda: dtf.add(60))
            .send(TimerTick())
            .check("Alarm")
            .send(TimerTick())
            .check()
            .act(lambda: dtf.add(10))
            .send(TimerTick())
            .check("Alarm")
            .send("Stop")
            .check("Alarm cancelled")
            .validate()
        )


