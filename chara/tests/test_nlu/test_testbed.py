import json
import tempfile
import wave
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
import numpy as np
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector
from grammatron import Utterance
from avatar.daemon import (
    BrainBoxService, ChatCommand, InitializationEvent, TextEvent, NLUTextEvent, RecognitionEvent, STTTrainingCommand,
    TemplatesRecognitionRequest, State, SoundEvent, StreamingSTTService, WhisperKenLMSTTService, IntentsPack, MAIN_CONTEXT,
)
from avatar.daemon.common import TickEvent, SoundStreamingStartEvent, SoundStreamingEndEvent
from avatar.messaging import AvatarDaemon, AvatarClient
from avatar.messaging.processing.filters import IProcessingFilter, ExceptionFilter, MaxTimeFilter
from chara.nlu.testbed import (
    TestbedIntents, TestbedService, TestbedChatService, ReportingNLUService, NLUReportEvent,
    SilenceSkippingWhisperKenLMSTTService, loudest_window_level, TestbedDaemonSettings, Stt, NLULatency,
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
        return [dict(text='Call Naruto', intent=CALL.get_name(), distance=0.05),
                dict(text="What's the weather like?", intent=WEATHER.get_name(), distance=0.4)]


class LlamaLoraServerMock(ISelfManagingDecider):
    def get_name(self):
        return 'LlamaLoraServer'

    def completion(self, task_name: str, prompt: str, max_tokens: int = 32):
        return f'\nintent: {_label(CALL)}\nperson: Naruto'


class ReportInChatFilter(IProcessingFilter):
    """The queue is empty while BrainBoxService is working, so the daemon must wait for the report itself"""
    def should_stop_on_queue(self, messages):
        return any(isinstance(m, ChatCommand) and m.type == ChatCommand.MessageType.system for m in messages)


class TestbedTestCase(TestCase):
    def run_testbed(self, stop, *messages):
        """Runs until a message of type `stop`, until the filter `stop` fires, or until the queue is empty if it is None"""
        with BrainBox.Api.serverless_test([ChromaMock(), LlamaLoraServerMock(), Collector()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(TestbedService(TestbedIntents.get_templates()))
            proc.rules.bind(TestbedChatService())
            proc.rules.bind(ReportingNLUService(slots_adapter='nlu-slots', brainbox_api=api))
            proc.rules.bind(BrainBoxService(api))
            if stop is None:
                return proc.debug_and_stop_by_empty_queue(InitializationEvent(), *messages).messages
            if isinstance(stop, IProcessingFilter):
                return proc.debug((InitializationEvent(), *messages), [stop, ExceptionFilter(), MaxTimeFilter(10)]).messages
            return proc.debug_and_stop_by_message_type(stop, InitializationEvent(), *messages).messages

    def test_initialization_trains_nlu(self):
        messages = self.run_testbed(STTTrainingCommand)
        templates = _last(messages, STTTrainingCommand).packs[0].templates
        self.assertEqual(len(TestbedIntents.get_templates()), len(templates))

    def test_typed_text_is_reported(self):
        messages = self.run_testbed(NLUReportEvent, TextEvent('Call Naruto'))
        report = _last(messages, NLUReportEvent)
        self.assertEqual('Call Naruto', report.text)
        self.assertEqual(2, len(report.neighbors))
        self.assertEqual(f'\nintent: {_label(CALL)}\nperson: Naruto', report.slots)
        self.assertIsInstance(report.recognition, Utterance)
        self.assertEqual({'person': 'Naruto'}, report.recognition.value)
        self.assertEqual(report.file_id, _last(messages, RecognitionEvent).file_id)

    def test_report_is_shown_in_chat(self):
        messages = self.run_testbed(ReportInChatFilter(), TextEvent('Call Naruto'))
        self.assertIn('recognized: TestbedIntents.call', _last(messages, ChatCommand).text)

    def test_typed_text_comes_before_its_report(self):
        messages = self.run_testbed(ReportInChatFilter(), TextEvent('Call Naruto'))
        chat = [m for m in messages if isinstance(m, ChatCommand)]
        self.assertEqual([ChatCommand.MessageType.from_user, ChatCommand.MessageType.system], [m.type for m in chat])

    def test_latency_of_recording(self):
        messages = self.run_testbed(
            NLUReportEvent,
            STTTrainingCommand([IntentsPack(MAIN_CONTEXT, tuple(TestbedIntents.get_templates()))]),
            SoundStreamingStartEvent('recording.wav'),
            SoundStreamingEndEvent('recording.wav', True),
            NLUTextEvent('recording.wav', 'Call Yuki', TemplatesRecognitionRequest()),
        )
        latency = _last(messages, NLUReportEvent).latency
        self.assertLessEqual(latency.recording_started, latency.recording_finished)
        self.assertLessEqual(latency.recording_finished, latency.stt_finished)
        self.assertLessEqual(latency.stt_finished, latency.chroma_finished)
        self.assertLessEqual(latency.stt_finished, latency.ner_finished)
        self.assertLessEqual(max(latency.chroma_finished, latency.ner_finished), latency.emitted)

    def test_recognized_speech_is_not_sent_again(self):
        messages = self.run_testbed(None, TextEvent('Call Naruto', file_id='recording.wav'))
        self.assertFalse(any(isinstance(m, NLUTextEvent) for m in messages))


class NLUReportTestCase(TestCase):
    def test_to_str(self):
        report = NLUReportEvent(
            'file', 'Call Naruto',
            [dict(text='Call Naruto', intent=CALL.get_name(), distance=0.05)],
            '\nintent: TestbedIntents.call\nperson: Naruto',
            CALL.utter(dict(person='Naruto')),
        )
        self.assertEqual(
            'text: Call Naruto\n'
            'neighbors:\n'
            '  0.050 TestbedIntents.call: Call Naruto\n'
            'slots: intent: TestbedIntents.call | person: Naruto\n'
            "recognized: TestbedIntents.call {'person': 'Naruto'}",
            report.to_str(),
        )

    def test_not_recognized(self):
        report = NLUReportEvent('file', 'Pass the salt', None, '\nintent: none', 'Pass the salt')
        self.assertEqual('text: Pass the salt\nslots: intent: none\nrecognized: nothing', report.to_str())

    def test_latency_to_str(self):
        t = datetime(2026, 11, 1, 12, 0, 0)
        latency = NLULatency(
            t, t + timedelta(seconds=2), t + timedelta(seconds=2.5),
            t + timedelta(seconds=2.6), t + timedelta(seconds=2.8), t + timedelta(seconds=3),
        )
        self.assertEqual(
            'latency: recorded 12:00:00.000-12:00:02.000 (2.00s) | stt +0.50s | chroma +0.10s | ner +0.30s | emitted +1.00s',
            latency.to_str(),
        )

    def test_latency_without_recording(self):
        t = datetime(2026, 11, 1, 12, 0, 0)
        latency = NLULatency(stt_finished=t, chroma_finished=t + timedelta(seconds=0.1), emitted=t)
        self.assertEqual('latency: chroma +0.10s', latency.to_str())

    def test_typed_text_request(self):
        event = TestbedService([]).on_typed_text(TextEvent('Call Naruto'))
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


def _report(file_id: str, text: str) -> NLUReportEvent:
    return NLUReportEvent(file_id, text, None, '\nintent: TestbedIntents.call\nperson: Naruto', CALL.utter(dict(person='Naruto')))


class TestbedChatServiceTestCase(TestCase):
    def test_report_of_recording_waits_for_its_text(self):
        service = TestbedChatService()
        self.assertEqual((), service.on_report(_report('recording.wav', 'Позвони Наруто')))
        message, report = service.on_event(TextEvent(CALL.utter(dict(person='Naruto')), file_id='recording.wav'))
        self.assertEqual(ChatCommand.MessageType.from_user, message.type)
        self.assertEqual('Позвони Наруто', message.text)
        self.assertEqual(ChatCommand.MessageType.system, report.type)
        self.assertIn("recognized: TestbedIntents.call {'person': 'Naruto'}", report.text)
        self.assertEqual({}, service.held_reports)

    def test_text_of_recording_waits_for_its_report(self):
        service = TestbedChatService()
        self.assertEqual((), service.on_event(TextEvent(CALL.utter(dict(person='Naruto')), file_id='recording.fixed.wav')))
        message, report = service.on_report(_report('recording.wav', 'Позвони Наруто'))
        self.assertEqual('Позвони Наруто', message.text)
        self.assertIn("recognized: TestbedIntents.call {'person': 'Naruto'}", report.text)
        self.assertEqual({}, service.held_texts)

    def test_streamed_recording_and_its_fixed_copy_are_paired(self):
        service = TestbedChatService()
        service.on_report(_report('recording.wav', 'Позвони Наруто'))
        message, report = service.on_event(TextEvent(CALL.utter(dict(person='Naruto')), file_id='recording.fixed.wav'))
        self.assertEqual('Позвони Наруто', message.text)

    def test_languages_of_recording_are_shown(self):
        events = [
            dict(text='Позвони Наруто', confidence=0.99, is_final=True, stream='ru'),
            dict(text='pozvoni naruto', confidence=0.95, is_final=True, stream='en'),
            dict(text='', confidence=1.0, is_final=True, stream='de'),
        ]
        line = "languages: ru 0.990 'Позвони Наруто' (chosen) | en 0.950 'pozvoni naruto' | de nothing\ntext:"
        with tempfile.TemporaryDirectory() as folder:
            name = 'recording.nemotron-stream.nemotron.transcribe_stream_languages.1.jsonl'
            (Path(folder)/name).write_text('\n'.join(json.dumps(e) for e in events))
            service = TestbedChatService(Path(folder))
            service.on_report(_report('recording.wav', 'Позвони Наруто'))
            message, report = service.on_event(TextEvent(CALL.utter(dict(person='Naruto')), file_id='recording.fixed.wav'))
            self.assertTrue(report.text.startswith(line))
            service.on_event(TextEvent(CALL.utter(dict(person='Naruto')), file_id='recording.fixed.wav'))
            message, report = service.on_report(_report('recording.wav', 'Позвони Наруто'))
            self.assertTrue(report.text.startswith(line))
            (report,) = service.on_report(_report('recording.wav', ''))
            self.assertTrue(report.text.startswith("languages: ru 0.990 'Позвони Наруто' | en 0.950 'pozvoni naruto' | de nothing\ntext:"))
            (report,) = service.on_report(_report('typed-1', 'Call Naruto'))
            self.assertTrue(report.text.startswith('text:'))

    def test_report_of_typed_text_is_shown_at_once(self):
        (command,) = TestbedChatService().on_report(_report('typed-1', 'Call Naruto'))
        self.assertEqual(ChatCommand.MessageType.system, command.type)

    def test_typed_text_is_shown_at_once(self):
        (message,) = TestbedChatService().on_event(TextEvent('Call Naruto'))
        self.assertEqual(ChatCommand.MessageType.from_user, message.type)

    def test_empty_recording_is_shown_at_once(self):
        service = TestbedChatService()
        (command,) = service.on_report(_report('recording.wav', ''))
        self.assertEqual(ChatCommand.MessageType.system, command.type)
        self.assertEqual({}, service.held_reports)

    def test_report_without_text_is_shown_after_a_while(self):
        service = TestbedChatService()
        service.on_report(_report('recording.wav', 'Позвони Наруто'))
        self.assertEqual((), service.on_tick(TickEvent(datetime.now())))
        (report,) = service.on_tick(TickEvent(datetime.now() + timedelta(seconds=10)))
        self.assertEqual(ChatCommand.MessageType.system, report.type)
        self.assertEqual({}, service.held_reports)

    def test_text_without_report_is_shown_after_a_while(self):
        service = TestbedChatService()
        service.on_event(TextEvent('Hello', file_id='recording.fixed.wav'))
        self.assertEqual((), service.on_tick(TickEvent(datetime.now())))
        (message,) = service.on_tick(TickEvent(datetime.now() + timedelta(seconds=10)))
        self.assertEqual(ChatCommand.MessageType.from_user, message.type)
        self.assertEqual({}, service.held_texts)

    def test_empty_typed_text_is_ignored(self):
        self.assertIsNone(TestbedService([]).on_typed_text(TextEvent('  ')))
        self.assertEqual((), TestbedChatService().on_event(TextEvent('')))


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
