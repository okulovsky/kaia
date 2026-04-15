from unittest import TestCase
from avatar.daemon import BrainBoxService, STTService, WhisperRecognitionSetup, VoskRecognitionSetup, IntentsPack, RhasspyRecognitionSetup
from avatar.messaging import AvatarDaemon, AvatarClient
from grammatron import Template, TemplatesCollection
from brainbox import BrainBox, ISelfManagingDecider


class WhisperMock(ISelfManagingDecider):
    def get_name(self):
        return 'Whisper'

    def transcribe_text(self, file, model=None, initial_prompt=None, options=None):
        return file


class VoskMock(ISelfManagingDecider):
    def get_name(self):
        return 'Vosk'

    def transcribe_to_string(self, file, model=None):
        return file


class RhasspyKaldiMock(ISelfManagingDecider):
    def get_name(self):
        return 'RhasspyKaldi'

    def train(self, name, language, sentences, custom_words=None):
        return 'OK'

    def transcribe(self, file, model=None):
        return {'fsticuffs': []}


class STTTestCase(TestCase):
    def test_stt(self):
        with BrainBox.Api.test([WhisperMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default())
            proc.rules.bind(STTService(WhisperRecognitionSetup()))
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(STTService.Command('test'))
            result = proc.debug_and_stop_by_message_type(STTService.Confirmation)

            message = result.messages[-1]
            self.assertIsInstance(message, STTService.Confirmation)
            self.assertEqual('test', message.recognition)

    def test_stt_request(self):
        with BrainBox.Api.test([WhisperMock(), VoskMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default())
            proc.rules.bind(STTService(WhisperRecognitionSetup()))
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(VoskRecognitionSetup('x'))
            proc.client.push(STTService.Command('vosk'))

            message_1 = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages[-1]
            self.assertEqual('vosk', message_1.recognition)

            proc.client.push(STTService.Command('whisper'))
            message_2 = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages[-1]
            self.assertEqual('whisper', message_2.recognition)

    def test_stt_kaldi_no_training(self):
        with BrainBox.Api.test([RhasspyKaldiMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(STTService(RhasspyRecognitionSetup('test_1')))
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(STTService.Command('file'))
            self.assertRaises(ValueError, lambda: proc.debug_and_stop_by_message_type(STTService.Confirmation))

    def test_stt_kaldi_training(self):
        class Collection1(TemplatesCollection):
            test_1 = Template("Test one")
        class Collection2(TemplatesCollection):
            test_2 = Template("Test two")

        packs = [
            IntentsPack('test_1', tuple(Collection1.get_templates()), {}, 'en'),
            IntentsPack('test_2', tuple(Collection2.get_templates()), {}, 'en')
        ]

        with BrainBox.Api.test([RhasspyKaldiMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            stt = STTService(RhasspyRecognitionSetup('test_2'))
            proc.rules.bind(stt)
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(STTService.RhasspyTrainingCommand(packs))
            proc.client.push(RhasspyRecognitionSetup('test_2'))
            proc.client.push(STTService.Command('file'))
            messages = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages

            self.assertIsInstance(messages[-1], STTService.Confirmation)
            self.assertIn('test_1', stt.handlers)
            self.assertIn('test_2', stt.handlers)
