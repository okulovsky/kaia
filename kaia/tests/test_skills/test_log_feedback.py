from unittest import TestCase
from kaia.skills.log_feedback_skill import LogFeedbackReplies, LogFeedbackIntents, LogFeedbackSkill
from kaia import  ErrorAnnouncement, WhisperOpenMicListen
from eaglesong.core import Automaton, Scenario, Return

def S():
    return Scenario(lambda: Automaton(LogFeedbackSkill().run, None), keep_listens_type_in_log=(WhisperOpenMicListen,))



class EchoSkillTestCase(TestCase):
    def test_echo(self):
        (
            S()
            .send(LogFeedbackIntents.report())
            .check(LogFeedbackReplies.report_request(), WhisperOpenMicListen)
            .send("Error")
            .check(
                lambda z: isinstance(z, ErrorAnnouncement) and z.content=="Error",
                LogFeedbackReplies.confirmation(),
                Return,
            )
            .validate()
        )
