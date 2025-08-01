from unittest import TestCase
from avatar.services.common.known_messages import TextInfo
from avatar.services import MockSoundService, BrainBoxService, VoiceoverService
from avatar.messaging import AvatarProcessor, TestStream, ThreadCollection

class VoiceoverServiceTestCase(TestCase):
    def test_voiceover(self):
        voiceover_service = VoiceoverService(VoiceoverService.MockTaskFactory())
        brainbox_service = BrainBoxService(VoiceoverService.brain_box_mock)
        sound_processor = MockSoundService()

        stream = TestStream()
        stream.put(VoiceoverService.Command(('a','b'), TextInfo('x','y')))
        app = AvatarProcessor(stream.create_client())
        app.rules.bind(voiceover_service)
        app.rules.bind(brainbox_service)
        app.rules.add(sound_processor)
        result = app.debug_and_stop_by_message_type(VoiceoverService.Confirmation)
        collection = ThreadCollection()
        collection.pull_changes(result.messages)
        topics = collection.get_top_topics()
        self.assertEqual(1, len(topics))
        topics[0].print()



