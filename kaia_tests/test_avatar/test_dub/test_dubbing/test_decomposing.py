from unittest import TestCase
from kaia.avatar.dub.sandbox.intents import Intents
from kaia.avatar.dub.languages.en import get_predefined_dubs
from kaia.avatar.dub.updater import DubbingTaskCreator
from datetime import timedelta



class DecomposeTestCase(TestCase):
    def test_1(self):
        tc = DubbingTaskCreator()
        sequences = tc.fragment(get_predefined_dubs(), Intents.get_templates(), 'test')
        dubber = tc.create_mock_dubber(sequences)
        ut = Intents.timer_create.utter(duration = timedelta(hours=2, minutes=37, seconds=55))
        result = dubber.decompose(ut)
        self.assertEqual(result[1], ut.to_str())
        self.assertEqual(result[1].replace(' ',''), ''.join(result[0]).replace(' ',''))

