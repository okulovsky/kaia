from unittest import TestCase
from datetime import datetime, timedelta, time
from eaglesong.core import Automaton, Scenario
from kaia.skills import TimeSkill, DateSkill, ByTheWayIntentTrigger, ByTheWaySkill, ByTheWayNotification
from kaia.skills import ScheduledTime
from kaia.dub.core import Utterance, Template
from kaia.skills.time import TimeIntents
from kaia.skills.date import DateIntents
from kaia.kaia import TestTimeFactory, KaiaAssistant, TimerTick

ut = Template('By the way, test').utter()

def get_scenario(*notification: ByTheWayNotification):
    factory = TestTimeFactory()
    btw = ByTheWaySkill(notification)
    assistant = KaiaAssistant(
        [
            TimeSkill(),
            DateSkill(),
            btw
        ]
    )
    assistant.datetime_factory = factory
    btw.assistant = assistant

    sc = Scenario(lambda: Automaton(assistant, None))
    return sc, factory



class ByTheWayTestCase(TestCase):
    def test_basic(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (ByTheWayIntentTrigger((TimeIntents.question,), 0),),
            ut,
            24
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .send(factory.tick())
            .check(ut)
            .validate()
        )

    def test_runs_after_proper_intent(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (ByTheWayIntentTrigger((TimeIntents.question,), 0),),
            ut,
            24
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(DateIntents.question.utter())
            .check(Utterance)
            .send(factory.tick())
            .check()
            .validate()
        )

    def test_respects_delay(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (ByTheWayIntentTrigger((TimeIntents.question,), 60),),
            ut,
            24
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check()
            .act_and_send(lambda: factory.shift(59).tick())
            .check()
            .act_and_send(lambda: factory.shift(1).tick())
            .check(ut)
            .validate()
        )

    def test_without_cooldown(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (ByTheWayIntentTrigger((TimeIntents.question,), 0),),
            ut,
            0
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check(ut)
            .act(lambda: factory.shift(1))
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check(ut)
            .validate()
        )

    def test_respects_cooldown(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (ByTheWayIntentTrigger((TimeIntents.question,), 0),),
            ut,
            1
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check(ut)
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check()
            .act_and_send(lambda: factory.shift(60*60*1))
            .send(TimeIntents.question.utter())
            .check(Utterance)
            .act_and_send(lambda: factory.tick())
            .check(ut)
            .validate()
        )

    def test_multiple_triggers(self):
        notification = ByTheWayNotification(
            ScheduledTime(time(0, 0, 0), timedelta(hours=24)),
            (
                ByTheWayIntentTrigger((TimeIntents.question,), 5),
                ByTheWayIntentTrigger((DateIntents.question,), 12)
            ),
            ut,
            0
        )
        sc, factory = get_scenario(notification)
        (
            sc
            .send(TimeIntents.question.utter())
            .act_and_send(lambda: factory.shift(4).tick())
            .check()
            .send(DateIntents.question.utter())
            .act_and_send(lambda: factory.shift(2).tick())
            .check() #Because second intent should have overriden the first
            .act_and_send(lambda: factory.shift(12).tick())
            .check(ut)
            .validate()
        )



