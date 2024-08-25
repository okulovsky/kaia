from kaia.kaia.core import SingleLineKaiaSkill, KaiaMessage
from unittest import TestCase
from kaia.kaia.skills.kaia_test_assistant import KaiaTestAssistant
from kaia.kaia.skills.exception_in_skill import ExceptionInSkillReplies
from kaia.eaglesong.core import Automaton, Scenario



class StatefulSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__()
        self.state = 0

    def run(self):
        yield self.state
        self.state+=1

    def should_start(self, input) -> False:
        return input=='A'

class ErroneousSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__()

    def should_start(self, input) -> False:
        return input=='B'

    def run(self):
        yield None
        raise ValueError()


class AssistantTestCase(TestCase):
    def test_error_handling(self):
        def create_assistant():
            assistant = KaiaTestAssistant([StatefulSkill(), ErroneousSkill()])
            assistant.raise_exceptions = False
            return Automaton(assistant, None)

        (Scenario(create_assistant)
         .send('A')
         .check(0)
         .send('A')
         .check(1)
         .send('B')
         .check(KaiaMessage, ExceptionInSkillReplies.answer.utter())
         .send('A')
         .check(2)
         .validate()
        )