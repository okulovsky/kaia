from unittest import TestCase
from kaia.eaglesong.core import Automaton, Scenario
from kaia.kaia.skills.help_skill import HelpReplies, HelpIntents, HelpSkill
from kaia.kaia.skills import KaiaTestAssistant, TimeSkill
from kaia.kaia.core import KaiaMessage

def create_automaton():
    skills = [TimeSkill(), help:= HelpSkill()]
    assistant = KaiaTestAssistant(skills)
    help.assistant = assistant
    return Automaton(assistant, None)



class ChangeImageTestCase(TestCase):
    def test_change_image(self):
        log = (
            Scenario(create_automaton)
            .send(HelpIntents.help.utter())
            .check(KaiaMessage, HelpReplies.help.utter().assertion)
            .validate()
            .log
        )
        self.assertEqual('TimeSkill\n- What time is it?\n- What is the time?\n\nHelpSkill\n- What can you do?\n', log[-1].response[0].text)

