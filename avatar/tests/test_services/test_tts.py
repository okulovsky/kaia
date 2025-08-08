from unittest import TestCase
from avatar.services.common.known_messages import TextInfo
from avatar.services import MockSoundService, BrainBoxService, TTSService, Confirmation
from avatar.messaging import AvatarProcessor, TestStream, ThreadCollection

class VoiceoverServiceTestCase(TestCase):
    def test_voiceover(self):
        voiceover_service = TTSService(TTSService.MockTaskFactory())
        brainbox_service = BrainBoxService(TTSService.brain_box_mock)
        sound_processor = MockSoundService()

        client = TestStream().create_client()
        client.put(TTSService.Command(('a','b'), TextInfo('x','y')))
        app = AvatarProcessor(client)
        app.rules.bind(voiceover_service)
        app.rules.bind(brainbox_service)
        app.rules.bind(sound_processor)
        result = app.debug_and_stop_by_message_type(Confirmation)
        collection = ThreadCollection()
        collection.pull_changes(result.messages)
        topics = collection.get_top_topics()
        self.assertEqual(1, len(topics))
        topics[0].print()



