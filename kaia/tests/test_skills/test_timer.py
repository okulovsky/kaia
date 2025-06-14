from unittest import TestCase
from datetime import datetime, timedelta
from eaglesong.core import Automaton, Scenario
from kaia.skills.timer_skill import TimerSkill, TimerReplies, TimerIntents
from kaia.skills.notification_skill import NotificationSkill, NotificationRegister
from kaia.kaia import TestTimeFactory, KaiaAssistant, TimerTick


def _factory(dtf, beautification):
    register = NotificationRegister(
        ('Alarm',),
        ('Alarm cancelled',) if beautification else None
    )
    notification = NotificationSkill([register], 10 if beautification else None)
    timer = TimerSkill(register, dtf)
    return Automaton(KaiaAssistant([timer, notification]), None)

def S(dtf: TestTimeFactory, with_after_audio = False):
    return Scenario(automaton_factory=lambda: _factory(dtf, with_after_audio))


class TestDate(TestCase):
    def test_timer_create(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=5)))
            .check(TimerReplies.timer_is_set.utter(duration=timedelta(minutes=5)))
            .send(TimerIntents.how_much_timers.utter())
            .check(
                TimerReplies.you_have.utter(amount=1) + TimerReplies.timer_description.utter(index=1, duration = timedelta(minutes=5)),
            )
            .act(lambda: dtf.shift(30))
            .send(TimerIntents.how_much_timers.utter())
            .check(
                TimerReplies.you_have(amount=1) + TimerReplies.timer_description(index=1, duration=timedelta(minutes=4, seconds=30)),
            )
            .send(TimerIntents.cancel_the_timer.utter())
            .check(
                TimerReplies.timer_is_cancelled.utter(),
            )
            .validate()
        )

    def test_timer_works(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=5)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=5)),
            )
            .act_and_send(lambda: dtf.shift(4*60+59).tick())
            .check()
            .act_and_send(lambda: dtf.shift(1).tick())
            .send(TimerTick())
            .check("Alarm")
            .send(TimerTick())
            .check("Alarm")
            .send("Stop")
            .check()
            .act_and_send(lambda: dtf.tick())
            .check()
            .validate()
        )

    def test_timer_beautification(self):
        dtf = TestTimeFactory()
        (
            S(dtf, True)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=1)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=1)),
            )
            .act_and_send(lambda: dtf.shift(60).tick())
            .check("Alarm")
            .act_and_send(lambda: dtf.tick())
            .check()
            .act_and_send(lambda: dtf.shift(10).tick())
            .check("Alarm")
            .send("Stop")
            .check("Alarm cancelled")
            .validate()
        )


