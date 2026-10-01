from unittest import TestCase


from avatar.daemon import STTIntegrationService, State, SoundEvent, STTService, SpeakerIdentificationService, TextEvent
from avatar.messaging import *
from grammatron import Template, Utterance

TEMPLATE = Template("Yes!")

class STTIntegrationTestCase(TestCase):
    def run_with_identification(self, response: str):
        proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        proc.rules.bind(STTIntegrationService(State(), True))
        result = proc.debug_and_stop_by_empty_queue(SoundEvent("file")).messages
        self.assertEqual(3, len(result))
        self.assertIsInstance(result[1], STTService.Command)
        self.assertIsInstance(result[2], SpeakerIdentificationService.Command)

        proc.client.push(STTService.Confirmation(response).as_confirmation_for(result[1]))
        proc.client.push(Confirmation("speaker").as_confirmation_for(result[2]))
        result = proc.debug_and_stop_by_empty_queue().messages
        return result[-1]

    def run_without_identification_and_get_all(self, response, emit_empty_recognitions: bool = False):
        proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        proc.rules.bind(STTIntegrationService(State(), False, emit_empty_recognitions))
        result = proc.debug_and_stop_by_empty_queue(SoundEvent("file")).messages
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[1], STTService.Command)

        proc.client.push(STTService.Confirmation(response).as_confirmation_for(result[1]))
        return proc.debug_and_stop_by_empty_queue().messages

    def run_without_identification(self, response):
        return self.run_without_identification_and_get_all(response)[-1]

    def test_text_with_id(self):
        result = self.run_with_identification("response")
        self.assertIsInstance(result, TextEvent)
        self.assertEqual('response', result.text)
        self.assertEqual('speaker', result.user)
        self.assertEqual('file', result.file_id)

    def test_text_without_id(self):
        result = self.run_without_identification("response")
        self.assertIsInstance(result, TextEvent)
        self.assertEqual('response', result.text)
        self.assertIsNone(result.user)
        self.assertEqual('file', result.file_id)

    def test_utterance_with_id(self):
        result = self.run_with_identification(TEMPLATE())
        self.assertIsInstance(result, TextEvent)
        self.assertIsInstance(result.text, Utterance)
        self.assertEqual(TEMPLATE.get_name(), result.text.template.get_name())
        self.assertEqual('speaker', result.user)
        self.assertEqual('file', result.file_id)

    def test_utterance_without_id(self):
        result = self.run_without_identification(TEMPLATE())
        self.assertIsInstance(result, TextEvent)
        self.assertIsInstance(result.text, Utterance)
        self.assertEqual(TEMPLATE.get_name(), result.text.template.get_name())
        self.assertIsNone(result.user)
        self.assertEqual('file', result.file_id)

    def test_empty_recognition_is_not_emitted(self):
        for response in ('', '   '):
            with self.subTest(response=repr(response)):
                result = self.run_without_identification_and_get_all(response)
                self.assertEqual([], [m for m in result if isinstance(m, TextEvent)])

    def test_empty_recognition_is_emitted_when_allowed(self):
        result = self.run_without_identification_and_get_all('', True)
        events = [m for m in result if isinstance(m, TextEvent)]
        self.assertEqual(1, len(events))
        self.assertEqual('', events[0].text)
