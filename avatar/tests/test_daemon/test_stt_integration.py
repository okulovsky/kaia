import io
import wave
from datetime import datetime, timedelta
from unittest import TestCase

from avatar.daemon import (
    STTIntegrationService, SoundEvent, SoundStreamingStartEvent, SoundStreamingEndEvent,
    RecognitionEvent, SpeakerIdentificationEvent, TextEvent,
)
from avatar.messaging import *
from foundation_kaia.misc import Loc
from grammatron import Template, Utterance

TEMPLATE = Template("Yes!")


def make_streamed_wav(rate: int = 8000, frames: int = 800) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b'\x01\x00' * frames)
    data = bytearray(buffer.getvalue())
    # While streaming, the sizes in the header are unknown
    data[4:8] = b'\x00\x00\x00\x00'
    data[40:44] = b'\x00\x00\x00\x00'
    return bytes(data)


class STTIntegrationTestCase(TestCase):
    def setUp(self):
        self.temp_folder = Loc.create_test_folder()
        self.folder = self.temp_folder.__enter__()
        self.original = make_streamed_wav()
        (self.folder / 'file.wav').write_bytes(self.original)

    def tearDown(self):
        self.temp_folder.__exit__(None, None, None)

    def create(self, speaker_identification: bool, emit_empty_recognitions: bool = False):
        self.service = STTIntegrationService(self.folder, 16000, speaker_identification, emit_empty_recognitions)
        self.proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        self.proc.rules.bind(self.service)

    def send(self, *messages):
        return self.proc.debug_and_stop_by_empty_queue(*messages).messages

    def record(self):
        return self.send(SoundStreamingStartEvent('file.wav'), SoundStreamingEndEvent('file.wav', True))

    def text_events(self, messages):
        return [m for m in messages if isinstance(m, TextEvent)]

    def run_flow(self, response, speaker_identification: bool, emit_empty_recognitions: bool = False):
        self.create(speaker_identification, emit_empty_recognitions)
        sound_events = [m for m in self.record() if isinstance(m, SoundEvent)]
        self.assertEqual(1, len(sound_events))
        self.assertEqual('file.fixed.wav', sound_events[0].file_id)
        messages = [RecognitionEvent('file.fixed.wav', response)]
        if speaker_identification:
            messages.append(SpeakerIdentificationEvent('file.fixed.wav', 'speaker'))
        return self.text_events(self.send(*messages))

    def test_file_is_fixed(self):
        self.create(False)
        self.record()
        self.assertEqual(self.original, (self.folder / 'file.wav').read_bytes())
        with wave.open(str(self.folder / 'file.fixed.wav')) as r:
            self.assertEqual(16000, r.getframerate())
            self.assertEqual(1600, r.getnframes())

    def test_text_with_id(self):
        events = self.run_flow('response', True)
        self.assertEqual(1, len(events))
        self.assertEqual('response', events[0].text)
        self.assertEqual('speaker', events[0].user)
        self.assertEqual('file.fixed.wav', events[0].file_id)
        self.assertEqual({}, self.service.recordings)

    def test_text_without_id(self):
        events = self.run_flow('response', False)
        self.assertEqual(1, len(events))
        self.assertEqual('response', events[0].text)
        self.assertIsNone(events[0].user)
        self.assertEqual('file.fixed.wav', events[0].file_id)

    def test_utterance_with_id(self):
        events = self.run_flow(TEMPLATE(), True)
        self.assertIsInstance(events[0].text, Utterance)
        self.assertEqual(TEMPLATE.get_name(), events[0].text.template.get_name())
        self.assertEqual('speaker', events[0].user)

    def test_waits_for_speaker(self):
        self.create(True)
        self.record()
        self.assertEqual([], self.text_events(self.send(RecognitionEvent('file.fixed.wav', 'response'))))
        events = self.text_events(self.send(SpeakerIdentificationEvent('file.fixed.wav', 'speaker')))
        self.assertEqual(1, len(events))

    def test_recognition_before_sound_event(self):
        self.create(False)
        self.send(SoundStreamingStartEvent('file.wav'), RecognitionEvent('file.wav', 'response'))
        messages = self.send(SoundStreamingEndEvent('file.wav', True))
        self.assertEqual(1, len([m for m in messages if isinstance(m, SoundEvent)]))
        events = self.text_events(messages)
        self.assertEqual(1, len(events))
        self.assertEqual('response', events[0].text)
        self.assertEqual('file.fixed.wav', events[0].file_id)

    def test_cancel(self):
        self.create(False)
        messages = self.send(SoundStreamingStartEvent('file.wav'), SoundStreamingEndEvent('file.wav', False))
        self.assertEqual([], [m for m in messages if isinstance(m, SoundEvent)])
        self.assertEqual({}, self.service.recordings)
        self.assertFalse((self.folder / 'file.fixed.wav').exists())

    def test_result_for_unknown_recording_is_ignored(self):
        self.create(False)
        self.assertEqual([], self.text_events(self.send(RecognitionEvent('other.fixed.wav', 'response'))))

    def test_error_result(self):
        self.create(True)
        self.record()
        self.assertRaises(ValueError, lambda: self.send(RecognitionEvent('file.fixed.wav', None, 'error')))
        self.assertEqual({}, self.service.recordings)

    def test_timeout_after_finish(self):
        self.create(True)
        self.record()
        self.send(RecognitionEvent('file.fixed.wav', 'response'))
        self.send(TickEvent(datetime.now()))
        self.assertIn('file.wav', self.service.recordings)
        self.assertRaises(ValueError, lambda: self.send(TickEvent(datetime.now() + timedelta(seconds=10))))
        self.assertEqual({}, self.service.recordings)

    def test_old_unfinished_recording_is_dropped(self):
        self.create(False)
        self.send(SoundStreamingStartEvent('file.wav'))
        self.send(TickEvent(datetime.now() + timedelta(seconds=10)))
        self.assertIn('file.wav', self.service.recordings)
        self.send(TickEvent(datetime.now() + timedelta(minutes=10)))
        self.assertEqual({}, self.service.recordings)

    def test_empty_recognition_is_not_emitted(self):
        for response in ('', '   '):
            with self.subTest(response=repr(response)):
                self.assertEqual([], self.run_flow(response, False))

    def test_empty_recognition_is_emitted_when_allowed(self):
        events = self.run_flow('', False, True)
        self.assertEqual(1, len(events))
        self.assertEqual('', events[0].text)
