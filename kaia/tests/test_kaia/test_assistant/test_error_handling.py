from kaia.kaia import SingleLineKaiaSkill, Message, KaiaAssistant
from kaia.kaia.assistant.exception_in_skill import ExceptionInSkillReplies
from unittest import TestCase
from eaglesong.core import Automaton, Scenario



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
            assistant = KaiaAssistant([StatefulSkill(), ErroneousSkill()])
            return Automaton(assistant, None)

        (Scenario(create_assistant)
         .send('A')
         .check(0)
         .send('A')
         .check(1)
         .send('B')
         .check(Message, ExceptionInSkillReplies.answer.utter())
         .send('A')
         .check(2)
         .validate()
        )