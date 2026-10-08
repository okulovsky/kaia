from datetime import timedelta
from enum import Enum
from unittest import TestCase
from grammatron import Template, VariableDub, TimedeltaDub, OrdinalDub, OptionsDub, Utterance
from avatar.daemon.stt_service.stt.nlu_setup import NluPostprocessor
from avatar.daemon.stt_service.stt.nlu_slots import slots_to_text, text_to_slots, slots_to_values


class Day(Enum):
    Today = 0
    Tomorrow = 1


SET_TIMER = Template(f"Set the timer for {VariableDub('duration', TimedeltaDub())}")
CANCEL_TIMER = Template('Cancel the timer', f"Cancel the {VariableDub('index', OrdinalDub(1, 10))} timer")
DATE = Template('What is the date?', f"What date is {VariableDub('delta', OptionsDub(Day))}?")
CHARACTER = Template(f"I want to talk with {VariableDub('character', OptionsDub(['Ocean', 'Forest']))}")
TIME = Template('What time is it?')


class SlotsFormatTestCase(TestCase):
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


def _result(text, intent, slots=None, distance=0.05):
    result = [
        dict(tags=dict(kind='text'), result=text),
        dict(tags=dict(kind='neighbors'), result=[dict(text=text, intent=intent, distance=distance)]),
    ]
    if slots is not None:
        result.append(dict(tags=dict(kind='slots'), result=slots))
    return result


class NluPostprocessorTestCase(TestCase):
    def setUp(self):
        templates = dict(set_timer=SET_TIMER, cancel_timer=CANCEL_TIMER, date=DATE, character=CHARACTER, time=TIME)
        self.with_slots = NluPostprocessor(templates, 0.18, with_slots=True)
        self.without_slots = NluPostprocessor(templates, 0.18)

    def recognize(self, postprocessor, *args, **kwargs):
        return postprocessor.postprocess(_result(*args, **kwargs)).recognition

    def test_slot_free_intent(self):
        recognition = self.recognize(self.with_slots, 'What time is it', 'time', '\n-')
        self.assertIsInstance(recognition, Utterance)

    def test_values_are_extracted(self):
        recognition = self.recognize(self.with_slots, 'Поставь таймер на пять минут', 'set_timer', '\nduration: 5m')
        self.assertIsInstance(recognition, Utterance)
        self.assertEqual(timedelta(minutes=5), recognition.value['duration'])

    def test_no_value_said(self):
        recognition = self.recognize(self.with_slots, 'Cancel the timer', 'cancel_timer', '\n-')
        self.assertIsInstance(recognition, Utterance)
        self.assertEqual({}, recognition.value)

    def test_missing_required_value_is_rejected(self):
        self.assertEqual('Set a timer', self.recognize(self.with_slots, 'Set a timer', 'set_timer', '\n-'))

    def test_unknown_option_is_rejected(self):
        self.assertEqual('Talk to Cliff', self.recognize(self.with_slots, 'Talk to Cliff', 'character', '\ncharacter: Cliff'))

    def test_garbage_from_model_is_rejected(self):
        self.assertEqual('Set a timer', self.recognize(self.with_slots, 'Set a timer', 'set_timer', 'five minutes'))

    def test_without_slots_model_variables_are_rejected(self):
        self.assertEqual('Cancel the timer', self.recognize(self.without_slots, 'Cancel the timer', 'cancel_timer'))
