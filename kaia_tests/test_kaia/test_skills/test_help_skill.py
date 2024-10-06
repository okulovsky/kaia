from unittest import TestCase
from kaia.eaglesong.core import Automaton, Scenario
from kaia.kaia.skills.help_skill import HelpReplies, HelpIntents, HelpSkill
from kaia.kaia.skills import TimeSkill
from kaia.kaia.core import KaiaMessage, KaiaAssistant

def create_automaton():
    skills = [TimeSkill(), help:= HelpSkill()]
    assistant = KaiaAssistant(skills)
    help.assistant = assistant
    return Automaton(assistant, None)

right_answer = '''TimeSkill: What time is it?, What is the time?

HelpSkill: What can you do?
'''

class ChangeImageTestCase(TestCase):
    def test_change_image(self):
        log = (
            Scenario(create_automaton)
            .send(HelpIntents.help.utter())
            .check(KaiaMessage, HelpReplies.help.utter())
            .validate()
            .log
        )
        print(f"'''{log[-1].response[0].text}'''")
        self.assertEqual(right_answer, log[-1].response[0].text)

