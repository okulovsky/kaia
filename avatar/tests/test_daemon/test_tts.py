from unittest import TestCase
from avatar.daemon import MockSoundService, BrainBoxService, TTSService, Confirmation
from avatar.daemon.tts_service import TTSSettings
from avatar.messaging import AvatarDaemon, AvatarClient
from brainbox import BrainBox, ISelfManagingDecider, File
from brainbox.deciders import Piper

class PiperMock(ISelfManagingDecider):
    def get_name(self):
        return 'Piper'

    def voiceover(self, text: str, **kwargs):
        return File(text + '.wav', text.encode('utf-8'))

class PiperTaskFactory(TTSService.TaskFactory):
    def create_task(self, s: str, info: TTSSettings) -> BrainBox.Task:
        return Piper.new_task().voiceover(s)

class VoiceoverServiceTestCase(TestCase):
    def test_voiceover(self):
        with BrainBox.Api.serverless_test([PiperMock()]) as api:
            voiceover_service = TTSService(PiperTaskFactory())
            brainbox_service = BrainBoxService(api)
            sound_processor = MockSoundService()

            client = AvatarClient.default()
            client.push(TTSService.Command(('a', 'b'), TTSService.Command.Settings('x', 'y')))
            proc = AvatarDaemon(client)
            proc.rules.bind(voiceover_service)
            proc.rules.bind(brainbox_service)
            proc.rules.bind(sound_processor)
            result = proc.debug_and_stop_by_message_type(Confirmation)
            self.assertEqual(1, len([m for m in result.messages if isinstance(m, Confirmation)]))
