from unittest import TestCase
from avatar.daemon import BrainBoxService, STTService, VoskRecognitionSetup, IntentsPack, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest, RecognitionEvent, SoundEvent, State
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
        with BrainBox.Api.serverless_test([WhisperMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default())
            proc.rules.bind(STTService(State(), default_request=FreeSpeechRecognitionRequest()))
            proc.rules.bind(BrainBoxService(api))

            result = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundEvent('test'))

            message = result.messages[-1]
            self.assertIsInstance(message, RecognitionEvent)
            self.assertEqual('test', message.file_id)
            self.assertEqual('test', message.recognition)
            self.assertIsNone(message.error)

    def test_stt_request(self):
        with BrainBox.Api.serverless_test([WhisperMock(), VoskMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default())
            stt = STTService(
                State(),
                templates_setup=lambda context: VoskRecognitionSetup(context),
                default_request=FreeSpeechRecognitionRequest(),
            )
            proc.rules.bind(stt)
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(TemplatesRecognitionRequest('x'))
            message_1 = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundEvent('vosk')).messages[-1]
            self.assertEqual('vosk', message_1.recognition)

            message_2 = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundEvent('whisper')).messages[-1]
            self.assertEqual('whisper', message_2.recognition)

    def test_stt_kaldi_no_training(self):
        with BrainBox.Api.serverless_test([RhasspyKaldiMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(STTService(State(), default_request=TemplatesRecognitionRequest('test_1')))
            proc.rules.bind(BrainBoxService(api))

            message = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundEvent('file')).messages[-1]
            self.assertIsNone(message.recognition)
            self.assertIsNotNone(message.error)

    def test_stt_kaldi_training(self):
        class Collection1(TemplatesCollection):
            test_1 = Template("Test one")
        class Collection2(TemplatesCollection):
            test_2 = Template("Test two")

        packs = [
            IntentsPack('test_1', tuple(Collection1.get_templates()), {}, 'en'),
            IntentsPack('test_2', tuple(Collection2.get_templates()), {}, 'en')
        ]

        with BrainBox.Api.serverless_test([RhasspyKaldiMock()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            stt = STTService(State())
            proc.rules.bind(stt)
            proc.rules.bind(BrainBoxService(api))

            proc.client.push(STTService.TrainingCommand(packs))
            proc.client.push(TemplatesRecognitionRequest('test_2'))
            messages = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundEvent('file')).messages

            self.assertIsInstance(messages[-1], RecognitionEvent)
            self.assertIn('test_1', stt.handlers)
            self.assertIn('test_2', stt.handlers)
