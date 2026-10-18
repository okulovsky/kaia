from datetime import timedelta
from enum import Enum
from unittest import TestCase
from grammatron import Template, VariableDub, TimedeltaDub, OrdinalDub, OptionsDub
from avatar.daemon.streaming_stt_service.nlu_slots import slots_to_text, text_to_slots, slots_to_values


class Day(Enum):
    Today = 0
    Tomorrow = 1


SET_TIMER = Template(f"Set the timer for {VariableDub('duration', TimedeltaDub())}")
CANCEL_TIMER = Template('Cancel the timer', f"Cancel the {VariableDub('index', OrdinalDub(1, 10))} timer")
DATE = Template('What is the date?', f"What date is {VariableDub('delta', OptionsDub(Day))}?")
CHARACTER = Template(f"I want to talk with {VariableDub('character', OptionsDub(['Ocean', 'Forest']))}")


class SlotsFormatTestCase(TestCase):
    def test_intent_line(self):
        self.assertEqual('\nintent: TimerIntents.set\nduration: 5m', slots_to_text(dict(duration='5m'), 'kaia.skills.TimerIntents.set'))
        self.assertEqual(dict(intent='TimerIntents.set', duration='5m'), text_to_slots('\nintent: TimerIntents.set\nduration: 5m'))

    def test_round_trip(self):
        slots = dict(duration='5m', index='2')
        self.assertEqual('\nduration: 5m\nindex: 2', slots_to_text(slots))
        self.assertEqual(slots, text_to_slots(slots_to_text(slots)))

    def test_empty(self):
        self.assertEqual('\n-', slots_to_text({}))
        self.assertEqual({}, text_to_slots('\n-'))

    def test_not_slots(self):
        self.assertIsNone(text_to_slots('set the timer for five minutes'))

    def test_values(self):
        self.assertEqual(dict(duration=timedelta(hours=1, minutes=30)), slots_to_values(SET_TIMER, dict(duration='1h 30m')))
        self.assertEqual(dict(index=3), slots_to_values(CANCEL_TIMER, dict(index='3')))
        self.assertEqual(dict(delta=Day.Tomorrow), slots_to_values(DATE, dict(delta='tomorrow')))
        self.assertEqual(dict(character='Forest'), slots_to_values(CHARACTER, dict(character='forest')))

    def test_values_that_do_not_fit(self):
        self.assertIsNone(slots_to_values(SET_TIMER, dict(duration='five minutes')))
        self.assertIsNone(slots_to_values(SET_TIMER, dict(duration='0m')))
        self.assertIsNone(slots_to_values(CANCEL_TIMER, dict(index='11')))
        self.assertIsNone(slots_to_values(CHARACTER, dict(character='Cliff')))
        self.assertIsNone(slots_to_values(CHARACTER, dict(dish='tea')))
