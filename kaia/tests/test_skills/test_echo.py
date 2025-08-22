from unittest import TestCase
from kaia.skills.echo_skill import EchoSkill, EchoIntents, EchoReplies, WhisperOpenMicListen
from eaglesong.core import Automaton, Scenario, Return

def S():
    return Scenario(lambda: Automaton(EchoSkill().run, None), keep_listens_type_in_log=(WhisperOpenMicListen,))



class EchoSkillTestCase(TestCase):
    def test_echo(self):
        (
            S()
            .send(EchoIntents.echo())
            .check(EchoReplies.echo_request(), WhisperOpenMicListen)
            .send("Make me a sandwich")
            .check('Make me a sandwich',Return)
            .validate()
        )
