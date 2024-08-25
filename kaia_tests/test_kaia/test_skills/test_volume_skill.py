from unittest import TestCase
from kaia.eaglesong.core import Automaton, Scenario
from kaia.kaia.skills.volume_skill import VolumeSkill, VolumeReplies, VolumeIntents
from kaia.kaia.skills import KaiaTestAssistant
from kaia.kaia.translators import VolumeTranslator
from kaia.kaia.core import KaiaMessage



def create_automaton(lst):
    skills = [VolumeSkill()]
    assistant = KaiaTestAssistant(skills)
    assistant = VolumeTranslator(assistant, lst.append, 0.1)
    return Automaton(assistant, None)



class VolumeTestCase(TestCase):
    def test_volume_skill(self):
        lst = []
        (
            Scenario(lambda:create_automaton(lst))
            .send(VolumeIntents.increase.utter())
            .check(KaiaMessage, VolumeReplies.sound_check.utter())
            .send(VolumeIntents.increase.utter())
            .check(KaiaMessage, VolumeReplies.sound_check.utter())
            .send(VolumeIntents.decrease.utter())
            .check(KaiaMessage, VolumeReplies.sound_check.utter())
            .validate()
        )
        self.assertListEqual([2, 3, 2], [int(10*c) for c in lst])


