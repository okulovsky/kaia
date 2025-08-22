from avatar.messaging import *
from avatar.daemon import ImageService, State
from avatar.daemon.common.content_manager import MediaLibraryManager, MediaLibrary
from avatar.daemon.common.known_messages import ChatCommand
from unittest import TestCase

def record_to_description(r: MediaLibrary.Record):
    return f'description {r.filename}'

characters = ('c0', 'c1')
activities = ('a0', 'a1')

class ImageServiceTestCase(TestCase):
    def setUp(self):
        records = [
            MediaLibrary.Record(
                f'{character}/{activity}/{index}',
                None,
                tags=dict(
                    character = character,
                    activity = activity,
                    index= index
                ),
                inline_content=f'{character}/{activity}/{index}'.encode('ascii')
            )
            for character in characters
            for activity in activities
            for index in ['i0','i1', 'i2']
        ]
        ml = MediaLibrary(tuple(records))
        self.manager = MediaLibraryManager(ml)


        self.state = State(character='c0', activity='a0')
        proc = AvatarDaemon(TestStream().create_client())
        proc.rules.bind(ImageService(self.state, None, self.manager, record_to_description))
        self.proc = proc


    def test_images_tags(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual(2, len(m))
        self.assertEqual({'character': 'c0', 'activity': 'a0', 'index': 'i0'}, m[-1].metadata)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual({'character': 'c0', 'activity': 'a0', 'index': 'i1'}, m[-1].metadata)

        self.state.activity = 'a1'
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual({'character': 'c0', 'activity': 'a1', 'index': 'i0'}, m[-1].metadata)

        self.state.character = 'c1'
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual({'character': 'c1', 'activity': 'a1', 'index': 'i0'}, m[-1].metadata)

    def test_images_hide_restore(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual({'character': 'c0', 'activity': 'a0', 'index': 'i0'}, m[-1].metadata)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.HideImageCommand()).messages
        self.assertIsNone(m[-1].metadata)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.RestoreImageCommand()).messages
        self.assertEqual({'character': 'c0', 'activity': 'a0', 'index': 'i0'}, m[-1].metadata)


    def test_feedback(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual({'character': 'c0', 'activity': 'a0', 'index': 'i0'}, m[-1].metadata)
        self.assertEqual('c0/a0/i0', m[-1].file_id)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageFeedback('good')).messages
        self.assertIsInstance(m[-1], Confirmation)

        feedback = self.manager.feedback_provider.load_feedback()
        self.assertEqual({'c0/a0/i0': {'seen': 1, 'good': 1}}, feedback)

    def test_description(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual('c0/a0/i0', m[-1].file_id)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageDescriptionCommand()).messages
        self.assertEqual('description c0/a0/i0', m[-1].text)
        self.assertEqual(ChatCommand.MessageType.system, m[-1].type)





