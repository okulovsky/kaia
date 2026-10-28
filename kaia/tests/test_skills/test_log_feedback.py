from unittest import TestCase
from kaia.skills.log_feedback_skill import LogFeedbackReplies, LogFeedbackIntents, LogFeedbackSkill
from kaia import  ErrorAnnouncement, FreeSpeechListen
from eaglesong.core import Automaton, Scenario, Return

def S():
    return Scenario(lambda: Automaton(LogFeedbackSkill().run, None), keep_listens_type_in_log=(FreeSpeechListen,))



class EchoSkillTestCase(TestCase):
    def test_echo(self):
        (
            S()
            .send(LogFeedbackIntents.report())
            .check(LogFeedbackReplies.report_request(), FreeSpeechListen)
            .send("Error")
            .check(
                lambda z: isinstance(z, ErrorAnnouncement) and z.content=="Error",
                LogFeedbackReplies.confirmation(),
                Return,
            )
            .validate()
        )
