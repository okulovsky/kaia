from unittest import TestCase
from eaglesong.core import Automaton, Scenario
from kaia.skills.help_skill import HelpReplies, HelpIntents, HelpSkill
from kaia.skills import TimeSkill, ChangeImageSkill
from avatar.daemon import ChatCommand


class ChangeImageTestCase(TestCase):
    def test_change_image(self):
        skills = [TimeSkill(), ChangeImageSkill()]

        log = (
            Scenario(lambda: Automaton(HelpSkill(skills).run, None))
            .send(HelpIntents.help.utter())
            .validate()
            .log
        )
        print(f"'''{log[-1].response[0].text}'''")


