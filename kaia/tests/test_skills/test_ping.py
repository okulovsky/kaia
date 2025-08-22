from unittest import TestCase
from kaia.skills.ping import PingSkill, PingIntents, PingReplies
from eaglesong.core import Automaton, Scenario, Return

def S():
    return Scenario(lambda: Automaton(PingSkill().run, None))



class PingSkillTestCase(TestCase):
    def test_ping(self):
        (
            S()
            .send(PingIntents.question())
            .check(PingReplies.answer(), Return)
            .validate()
        )
