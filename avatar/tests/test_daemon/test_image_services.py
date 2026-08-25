import json
import zipfile
from avatar.messaging import *
from avatar.daemon import ImageService, State, ChatCommand
from avatar.daemon.image_service.media_library import MediaLibrary
from avatar.daemon.common.known_messages import InitializationEvent
from unittest import TestCase
from foundation_kaia.misc import Loc

class _FakeCache:
    def upload(self, path, content):
        pass

class _FakeApi:
    def __init__(self):
        self.cache = _FakeCache()

characters = ('c0', 'c1')
activities = ('a0', 'a1')

class ImageServiceTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
        records = [
            {'path': f'{character}/{activity}/{index}',
             'tags': dict(character=character, activity=activity, index=index)}
            for character in characters
            for activity in activities
            for index in ['i0', 'i1', 'i2']
        ]
        with zipfile.ZipFile(self.folder/'media_library.zip', 'w') as zp:
            zp.writestr('records.json', json.dumps(records))

        self.state = State(character='c0', activity='a0')
        proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        self.service = ImageService(self.state, None)
        self.service.set_resources_folder(self.folder)
        self.service.on_initialize(InitializationEvent())
        proc.rules.bind(self.service)
        self.proc = proc

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def _records_for(self, character, activity):
        return [
            r for r in self.service.media_library.records
            if r.tags['character'] == character and r.tags['activity'] == activity
        ]

    def test_photo_album_shows_a_record_from_the_set(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(self._records_for('c0', 'a0'))).messages
        self.assertEqual(2, len(m))
        self.assertEqual('c0', m[-1].metadata['character'])
        self.assertEqual('a0', m[-1].metadata['activity'])

    def test_photo_album_command_replaces_the_current_set(self):
        self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(self._records_for('c0', 'a0')))
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(self._records_for('c1', 'a1'))).messages
        self.assertEqual('c1', m[-1].metadata['character'])
        self.assertEqual('a1', m[-1].metadata['activity'])

    def test_new_image_avoids_repeats_until_the_set_is_exhausted(self):
        three_records = self._records_for('c0', 'a0')
        self.assertEqual(3, len(three_records))
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(three_records)).messages
        shown = {m[-1].file_id}
        for _ in range(2):
            m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
            shown.add(m[-1].file_id)
        self.assertEqual(3, len(shown))

    def test_new_image_without_a_set_shows_empty_image(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
        self.assertIsNone(m[-1].metadata)
        self.assertEqual('empty_image.png', m[-1].file_id)

    def test_bad_feedback_excludes_the_record_going_forward(self):
        two_records = self._records_for('c0', 'a0')[:2]
        self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(two_records))
        banned_path = self.service.last_base_image_record.path

        self.proc.debug_and_stop_by_empty_queue(ImageService.ImageFeedback('bad'))
        for _ in range(5):
            m = self.proc.debug_and_stop_by_empty_queue(ImageService.NewImageCommand()).messages
            self.assertNotEqual(banned_path, m[-1].file_id)

    def test_images_hide_restore(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(self._records_for('c0', 'a0'))).messages
        shown_path = m[-1].file_id

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.HideImageCommand()).messages
        self.assertIsNone(m[-1].metadata)

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.RestoreImageCommand()).messages
        self.assertEqual(shown_path, m[-1].file_id)

    def test_feedback(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(self._records_for('c0', 'a0'))).messages
        shown_path = m[-1].file_id

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageFeedback('good')).messages
        self.assertIsInstance(m[-1], Confirmation)

        feedback = self.service.feedback_provider.load_feedback()
        self.assertEqual({'seen': 1, 'good': 1}, feedback[shown_path])

    def test_variant_feedback_is_recorded_on_variant_and_rolled_up_to_base(self):
        base_records = self._records_for('c0', 'a0')[:1]
        self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(base_records))
        base_path = self.service.last_base_image_record.path

        variant_path = f'{base_path}__goth'
        variant_zip = self.folder / 'variants.zip'
        with zipfile.ZipFile(variant_zip, 'w') as zp:
            zp.writestr(variant_path, b'goth-variant-bytes')
        variant_record = MediaLibrary.Record(variant_path, {'original': base_path, 'variant_type': 'goth'}, variant_zip)
        self.service.media_library.records.append(variant_record)
        self.service.api = _FakeApi()

        self.proc.debug_and_stop_by_empty_queue(ImageService.VariantRequest('goth'))
        self.assertEqual(variant_path, self.service.last_shown_image_record.path)
        self.assertEqual(base_path, self.service.last_base_image_record.path)

        self.proc.debug_and_stop_by_empty_queue(ImageService.ImageFeedback('good'))

        feedback = self.service.feedback_provider.load_feedback()
        self.assertEqual(1, feedback[variant_path]['good'])
        self.assertEqual(1, feedback[base_path]['variant_goth_good'])

    def test_description_without_shown_image_errors(self):
        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageDescriptionCommand()).messages
        self.assertIsInstance(m[-1], Confirmation)
        self.assertIsNotNone(m[-1].error)

    def test_description_shows_non_none_tags(self):
        record = self._records_for('c0', 'a0')[0]
        record.tags['index'] = None
        self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand([record]))

        m = self.proc.debug_and_stop_by_empty_queue(ImageService.ImageDescriptionCommand()).messages
        self.assertIsInstance(m[-1], ChatCommand)
        self.assertEqual('c0, a0', m[-1].text)

    def test_variant_feedback_does_not_pollute_base_when_base_is_shown(self):
        base_records = self._records_for('c0', 'a0')[:1]
        self.proc.debug_and_stop_by_empty_queue(ImageService.PhotoAlbumCommand(base_records))
        base_path = self.service.last_base_image_record.path

        self.proc.debug_and_stop_by_empty_queue(ImageService.ImageFeedback('good'))

        feedback = self.service.feedback_provider.load_feedback()
        self.assertEqual(1, feedback[base_path]['good'])
        self.assertFalse(any(key.startswith('variant_') for key in feedback[base_path]))
