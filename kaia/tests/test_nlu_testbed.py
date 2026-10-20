from types import SimpleNamespace
from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector
from grammatron import Utterance
from avatar.daemon import (
    BrainBoxService, ChatCommand, InitializationEvent, TextEvent, NLUTextEvent, RecognitionEvent, STTTrainingCommand,
    TemplatesRecognitionRequest, State, StreamingSTTService, WhisperKenLMSTTService,
)
from avatar.messaging import AvatarDaemon, AvatarClient
from kaia.nlu_testbed import TestbedIntents, TestbedService, ReportingNLUService, NLUReportEvent, TestbedDaemonSettings, Stt

CALL = TestbedIntents.call
WEATHER = TestbedIntents.weather


def _last(messages, type):
    return [m for m in messages if isinstance(m, type)][-1]


def _label(template):
    return '.'.join(template.get_name().split('.')[-2:])


class ChromaMock(ISelfManagingDecider):
    def get_name(self):
        return 'Chroma'

    def find_neighbors(self, text: str, k: int = 5, collection_name: str | None = None) -> list[dict]:
        return [dict(text='Call Yuki', intent=CALL.get_name(), distance=0.05),
                dict(text="What's the weather like?", intent=WEATHER.get_name(), distance=0.4)]


class LlamaLoraServerMock(ISelfManagingDecider):
    def get_name(self):
        return 'LlamaLoraServer'

    def completion(self, task_name: str, prompt: str, max_tokens: int = 32):
        return f'\nintent: {_label(CALL)}\nperson: Yuki'


class TestbedTestCase(TestCase):
    def run_testbed(self, stop_type, *messages):
        """Runs until a message of `stop_type`, or until the queue is empty if it is None"""
        with BrainBox.Api.serverless_test([ChromaMock(), LlamaLoraServerMock(), Collector()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(TestbedService(TestbedIntents.get_templates()))
            proc.rules.bind(ReportingNLUService(slots_adapter='nlu-slots'))
            proc.rules.bind(BrainBoxService(api))
            if stop_type is None:
                return proc.debug_and_stop_by_empty_queue(InitializationEvent(), *messages).messages
            return proc.debug_and_stop_by_message_type(stop_type, InitializationEvent(), *messages).messages

    def test_initialization_trains_nlu(self):
        messages = self.run_testbed(STTTrainingCommand)
        templates = _last(messages, STTTrainingCommand).packs[0].templates
        self.assertEqual(len(TestbedIntents.get_templates()), len(templates))

    def test_typed_text_is_reported(self):
        messages = self.run_testbed(NLUReportEvent, TextEvent('Call Yuki'))
        report = _last(messages, NLUReportEvent)
        self.assertEqual('Call Yuki', report.text)
        self.assertEqual(2, len(report.neighbors))
        self.assertEqual(f'\nintent: {_label(CALL)}\nperson: Yuki', report.slots)
        self.assertIsInstance(report.recognition, Utterance)
        self.assertEqual({'person': 'Yuki'}, report.recognition.value)
        self.assertEqual(report.file_id, _last(messages, RecognitionEvent).file_id)

    def test_report_is_shown_in_chat(self):
        messages = self.run_testbed(None, TextEvent('Call Yuki'))
        self.assertIn('recognized: TestbedIntents.call', _last(messages, ChatCommand).text)

    def test_recognized_speech_is_not_sent_again(self):
        messages = self.run_testbed(None, TextEvent('Call Yuki', file_id='recording.wav'))
        self.assertFalse(any(isinstance(m, NLUTextEvent) for m in messages))


class NLUReportTestCase(TestCase):
    def test_to_str(self):
        report = NLUReportEvent(
            'file', 'Call Yuki',
            [dict(text='Call Yuki', intent=CALL.get_name(), distance=0.05)],
            '\nintent: TestbedIntents.call\nperson: Yuki',
            CALL.utter(dict(person='Yuki')),
        )
        self.assertEqual(
            'text: Call Yuki\n'
            'neighbors:\n'
            '  0.050 TestbedIntents.call: Call Yuki\n'
            'slots: intent: TestbedIntents.call | person: Yuki\n'
            "recognized: TestbedIntents.call {'person': 'Yuki'}",
            report.to_str(),
        )

    def test_not_recognized(self):
        report = NLUReportEvent('file', 'Pass the salt', None, '\nintent: none', 'Pass the salt')
        self.assertEqual('text: Pass the salt\nslots: intent: none\nrecognized: nothing', report.to_str())

    def test_typed_text_request(self):
        event = TestbedService([]).on_typed_text(TextEvent('Call Yuki'))
        self.assertEqual(TemplatesRecognitionRequest(), event.request)
        self.assertTrue(event.file_id.startswith('typed-'))


class SttTestCase(TestCase):
    def test_each_stt_creates_its_service(self):
        app = SimpleNamespace(brainbox_cache_folder='cache')
        services = {stt: TestbedDaemonSettings(stt=stt).create_stt_service(app, State()) for stt in Stt.ALL}
        self.assertIsNone(services[Stt.NEMOTRON].languages)
        self.assertEqual(Stt.LANGUAGES, services[Stt.NEMOTRON_LANGUAGES].languages)
        self.assertIsInstance(services[Stt.NEMOTRON_LANGUAGES], StreamingSTTService)
        self.assertIsInstance(services[Stt.WHISPER_KENLM], WhisperKenLMSTTService)

    def test_unknown_stt(self):
        with self.assertRaises(ValueError):
            TestbedDaemonSettings(stt='vosk').create_stt_service(SimpleNamespace(brainbox_cache_folder='cache'), State())
