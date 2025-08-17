from unittest import TestCase
from eaglesong.core import Automaton, Scenario
from kaia.skills.volume_skill import VolumeSkill, VolumeReplies, VolumeIntents
from avatar.daemon import VolumeControlService
from eaglesong import Return


class VolumeTestCase(TestCase):
    def test_volume_skill(self):
        skill = VolumeSkill()
        (
            Scenario(lambda:Automaton(skill.run,None))
            .send(VolumeIntents.increase.utter())
            .check(VolumeControlService.Command, VolumeReplies.sound_check.utter(), Return)
            .send(VolumeIntents.decrease.utter())
            .check(VolumeControlService.Command, VolumeReplies.sound_check.utter(), Return)
            .validate()
        )


