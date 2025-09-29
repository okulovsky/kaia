import os

import yo_fluq

from avatar.messaging import *
from avatar.daemon import ImageService, State
from avatar.daemon.common.content_manager import MediaLibraryManager, MediaLibrary, NewContentStrategy
from avatar.daemon.common.known_messages import ChatCommand, InitializationEvent
from unittest import TestCase
from foundation_kaia.misc import Loc

def record_to_description(r: MediaLibrary.Record):
    return f'description {r.filename}'

characters = ('c0', 'c1')
activities = ('a0', 'a1')

class ImageServiceTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
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
        ml.save(self.folder/'media_library.zip')

        self.state = State(character='c0', activity='a0')
        proc = AvatarDaemon(TestStream().create_client())
        self.service = ImageService(self.state, None, NewContentStrategy(False), record_to_description)
        self.service.set_resources_folder(self.folder)
        self.service.on_initialize(InitializationEvent())
        proc.rules.bind(self.service)
        self.proc = proc

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

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

        feedback = self.service.media_library_manager.feedback_provider.load_feedback()
        self.assertEqual({'c0/a0/i0': {'seen': 1, 'good': 1}}, feedback)

    def test_description(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertEqual('c0/a0/i0', m[-1].file_id)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageDescriptionCommand()).messages
        self.assertEqual('description c0/a0/i0', m[-1].text)
        self.assertEqual(ChatCommand.MessageType.system, m[-1].type)





