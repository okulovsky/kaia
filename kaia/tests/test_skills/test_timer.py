from unittest import TestCase
from datetime import datetime, timedelta
from eaglesong.core import Automaton, Scenario
from kaia.skills.timer_skill import TimerSkill, TimerReplies, TimerIntents
from kaia.skills.notification_skill import NotificationSkill, NotificationRegister
from kaia import KaiaAssistant
from avatar.daemon import ChatCommand
from avatar.utils import TestTimeFactory
from grammatron import UtterancesSequence



def _factory(dtf, beautification):
    register = NotificationRegister(
        (ChatCommand('Alarm'),),
        (ChatCommand('Alarm cancelled'),) if beautification else None
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
            .act_and_send(lambda: dtf.shift(4*60+59).event())
            .check()
            .act_and_send(lambda: dtf.shift(1).event())
            .check(lambda z: z.text=="Alarm")
            .act_and_send(lambda: dtf.shift(1).event())
            .check(lambda z: z.text=="Alarm")
            .send("Stop")
            .check()
            .act_and_send(lambda: dtf.event())
            .check()
            .validate()
        )

    def test_several_timers(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=5)))
            .check(
                TimerReplies.timer_is_set.utter(duration=timedelta(minutes=5)),
            )
            .send(TimerIntents.set_the_timer.utter(duration=timedelta(minutes=6)))
            .check(
                TimerReplies.timer_is_set.utter(index=2, duration=timedelta(minutes=6))
            )
            .send(TimerIntents.how_much_timers.utter())
            .check(
                lambda z: isinstance(z, UtterancesSequence) and z.utterances[0].value['amount'] == 2
            )
            .send(TimerIntents.how_much_time_left())
            .check(
                lambda z: isinstance(z, UtterancesSequence) and z.utterances[0].value['amount'] == 2
            )
            .send(TimerIntents.cancel_the_timer())
            .check(TimerReplies.which_timer_error(2))
            .send(TimerIntents.cancel_the_timer(1))
            .check(TimerReplies.timer_is_cancelled(index=1))
            .send(TimerIntents.how_much_time_left())
            .check(TimerReplies.timer_description(duration=timedelta(minutes=6)))
            .validate()
        )


