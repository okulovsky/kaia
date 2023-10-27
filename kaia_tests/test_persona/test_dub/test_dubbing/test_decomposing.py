from unittest import TestCase
from demos.persona.intents import Intents
from kaia.persona.dub.languages.en import DubbingTaskCreator, get_predefined_dubs, CardinalDub, OrdinalDub, TimedeltaDub, DubbingPack
from pprint import pprint

tc = DubbingTaskCreator()
sequences = tc.fragment(get_predefined_dubs(), Intents.get_templates(), 'test')
dubber = DubbingPack(tc.create_mock_fragments(sequences,True)).create_dubber()

class DecomposeTestCase(TestCase):
    def test_1(self):
        pprint(list(dubber.vocabulary))
        result = dubber.decompose('Set the seventh timer for two hours, twenty seven minutes and fifty five seconds',Intents.timer_create)
        print(result)
