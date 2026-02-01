from unittest import TestCase
from eaglesong.core import Automaton, Scenario
from kaia.skills.ping import PingSkill, PingIntents, PingReplies
from kaia.skills.recognition_feedback import RecognitionFeedbackSkill, RecognitionFeedbackIntents, RecognitionFeedbackReplies
from kaia.skills.walk_in_skill import WalkInSkill, WalkInAnnouncement
from kaia import KaiaAssistant, StateTranslator, KaiaContext
from avatar.daemon import TextCommand, TextEvent, SpeakerIdentificationService, UserWalkInService
from avatar.utils import TestTimeFactory
from grammatron import Utterance
from eaglesong import IAsserter
from datetime import time, timedelta, datetime
from foundation_kaia.misc import EveryDayRepetition





def _factory(dtf):
    ping = PingSkill()
    feedback = RecognitionFeedbackSkill(['A', 'B'], 10, dtf)
    walkin = WalkInSkill([
        WalkInAnnouncement('A', time(0), time(23), EveryDayRepetition(), timedelta(minutes=0), "Announcement"),
    ])
    assistant = KaiaAssistant([ping, feedback, walkin])
    assistant = StateTranslator(assistant, dtf)
    context = KaiaContext(None)
    return Automaton(assistant, context)

def S(dtf: TestTimeFactory):
    return Scenario(automaton_factory=lambda: _factory(dtf))


class TCA(IAsserter):
    def __init__(self, utterance: Utterance|str, user: str):
        self.utterance = utterance
        self.user = user

    def assertion(self, actual, test_case: TestCase):
        test_case.assertIsInstance(actual, TextCommand)
        test_case.assertIsInstance(actual.text, type(self.utterance))
        if isinstance(self.utterance, Utterance):
            self.utterance.assertion(actual.text, test_case)
        else:
            test_case.assertEqual(self.utterance, actual.text)
        test_case.assertEqual(actual.user, self.user)


class TA(IAsserter):
    def __init__(self, is_audio: bool, user: str, file: str):
        self.is_audio = is_audio
        self.user = user
        self.file = file

    def assertion(self, actual, test_case: TestCase):
        if self.is_audio:
            test_case.assertIsInstance(actual, SpeakerIdentificationService.Train)
        else:
            test_case.assertIsInstance(actual, UserWalkInService.Train)
        test_case.assertEqual(actual.file_id, self.file)
        test_case.assertEqual(actual.actual_user, self.user)


class TestDate(TestCase):
    def test_audio_retraining(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TextEvent(PingIntents.question(), 'A', 'file'))
            .check(TCA(PingReplies.answer(), 'A'))
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('B'), 'B', 'file_1'))
            .check(TA(True, 'B', 'file'), TCA(RecognitionFeedbackReplies.fix_audio(), 'B'))
            .validate()
        )

    def test_image_retraining(self):
        dtf = TestTimeFactory(datetime(2020,1,1,12,00))
        (
            S(dtf)
            .send(UserWalkInService.Event('A', 'file_1'))
            .check(TCA("Announcement", "A"))
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('B'), 'A', 'file_2'))
            .check(TA(False, "B", "file_1"), TCA(RecognitionFeedbackReplies.fix_image(), 'A'))
            .validate()
        )

    def test_training_not_distorted_by_unproductive_commands(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TextEvent(PingIntents.question(), 'A', 'file'))
            .check(TCA(PingReplies.answer(), 'A'))
            .send(UserWalkInService.Event('B', 'file_2'))
            .check()
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('B'), 'B', 'file_1'))
            .check(TA(True, 'B', 'file'), TCA(RecognitionFeedbackReplies.fix_audio(), 'B'))
            .validate()
        )

    def test_no_retrain_if_no_error(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TextEvent(PingIntents.question(), 'A', 'file'))
            .check(TCA(PingReplies.answer(), 'A'))
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('A'), 'A', 'file_1'))
            .check(TCA(RecognitionFeedbackReplies.i_know(), 'A'))
            .validate()
        )


    def test_no_retrain_if_no_context(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('A'), 'A', 'file_1'))
            .check(TCA(RecognitionFeedbackReplies.error(), 'A'))
            .validate()
        )

    def test_no_retrain_if_too_much_time_passed(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(TextEvent(PingIntents.question(), 'A', 'file'))
            .check(TCA(PingReplies.answer(), 'A'))
            .act(lambda: dtf.shift(11))
            .send(TextEvent(RecognitionFeedbackIntents.misrecognition('A'), 'A', 'file_1'))
            .check(TCA(RecognitionFeedbackReplies.error(), 'A'))
            .validate()
        )