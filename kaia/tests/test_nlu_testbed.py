import tempfile
import wave
from pathlib import Path
from unittest import TestCase
import numpy as np
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector
from grammatron import Utterance
from avatar.daemon import (
    BrainBoxService, ChatCommand, InitializationEvent, TextEvent, NLUTextEvent, RecognitionEvent, STTTrainingCommand,
    TemplatesRecognitionRequest, State, SoundEvent,
)
from avatar.messaging import AvatarDaemon, AvatarClient
from kaia.nlu_testbed import (
    TestbedIntents, TestbedService, TestbedChatService, ReportingNLUService, NLUReportEvent,
    SilenceSkippingWhisperKenLMSTTService, loudest_window_level,
)

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
            proc.rules.bind(TestbedChatService())
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

    def test_typed_text_comes_before_its_report(self):
        messages = self.run_testbed(None, TextEvent('Call Yuki'))
        chat = [m for m in messages if isinstance(m, ChatCommand)]
        self.assertEqual([ChatCommand.MessageType.from_user, ChatCommand.MessageType.system], [m.type for m in chat])

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


def _report(file_id: str, text: str) -> NLUReportEvent:
    return NLUReportEvent(file_id, text, None, '\nintent: TestbedIntents.call\nperson: Yuki', CALL.utter(dict(person='Yuki')))


class TestbedChatServiceTestCase(TestCase):
    def test_report_of_recording_waits_for_its_text(self):
        service = TestbedChatService()
        self.assertIsNone(service.on_report(_report('recording.wav', 'Позвони Юки')))
        message, report = service.on_event(TextEvent(CALL.utter(dict(person='Yuki')), file_id='recording.wav'))
        self.assertEqual(ChatCommand.MessageType.from_user, message.type)
        self.assertEqual('Позвони Юки', message.text)
        self.assertEqual(ChatCommand.MessageType.system, report.type)
        self.assertIn("recognized: TestbedIntents.call {'person': 'Yuki'}", report.text)
        self.assertEqual({}, service.held_reports)

    def test_report_of_typed_text_is_shown_at_once(self):
        command = TestbedChatService().on_report(_report('typed-1', 'Call Yuki'))
        self.assertEqual(ChatCommand.MessageType.system, command.type)

    def test_empty_recording_is_not_shown(self):
        service = TestbedChatService()
        self.assertIsNone(service.on_report(_report('recording.wav', '')))
        self.assertEqual({}, service.held_reports)

    def test_text_without_report(self):
        (message,) = TestbedChatService().on_event(TextEvent('Hello', file_id='recording.wav'))
        self.assertEqual(ChatCommand.MessageType.from_user, message.type)


def _write_wav(path: Path, samples: np.ndarray):
    with wave.open(str(path), 'wb') as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(16000)
        file.writeframes((samples * 32767).astype(np.int16).tobytes())


class SilenceSkippingTestCase(TestCase):
    def test_loudest_window_level(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'a.wav'
            samples = np.zeros(16000)
            samples[8192:8704] = 0.5
            _write_wav(path, samples)
            self.assertAlmostEqual(0.5, loudest_window_level(path), places=2)

    def test_silence_is_not_sent_to_whisper(self):
        with tempfile.TemporaryDirectory() as folder:
            _write_wav(Path(folder) / 'silence.wav', np.full(8000, 0.001))
            service = SilenceSkippingWhisperKenLMSTTService(State(), folder)
            event = service.transcribe(SoundEvent('silence.wav'))
            self.assertEqual('', event.text)
            self.assertEqual('silence.wav', event.file_id)
            self.assertEqual(TemplatesRecognitionRequest(), event.request)
