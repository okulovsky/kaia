import datetime
import json
import zipfile

from avatar.messaging import *
from avatar.daemon import NarrationService, State, SimpleNarrator
from avatar.daemon.common.known_messages import TextCommand
from avatar.daemon.common.content_manager import NewContentStrategy
from avatar.daemon.image_service import MediaLibrary, MediaLibraryManager, PhotoAlbumCommand
from unittest import TestCase
from foundation_kaia.misc import Loc

characters = ('c0', 'c1', 'c2')
activities = ('a0', 'a1', 'a2')


class NarrationTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
        records = [
            {'path': f'{c}/{a}', 'tags': dict(character=c, activity=a)}
            for c in characters for a in activities
        ]
        with zipfile.ZipFile(self.folder/'media_library.zip', 'w') as zp:
            zp.writestr('records.json', json.dumps(records))
        media_library = MediaLibrary.from_folder(self.folder, 'media_library', '.zip')
        content_manager = MediaLibraryManager(media_library, strategy=NewContentStrategy(randomize=False))

        self.proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        self.state = State(character='c1', activity='a1')
        self.proc.rules.bind(NarrationService(
            self.state,
            SimpleNarrator(content_manager, randomize=False),
            TextCommand('hello'),
            60,
        ))

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def test_random_character_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand()).messages
        self.assertEqual(4, len(m))
        self.assertEqual('c0', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], PhotoAlbumCommand)
        self.assertEqual(1, len(m[1].records))
        self.assertIsInstance(m[2], TextCommand)

    def test_character_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand('c2')).messages
        self.assertEqual(4, len(m))
        self.assertEqual('c2', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], PhotoAlbumCommand)
        self.assertIsInstance(m[2], TextCommand)

    def test_activity_change(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeActivityCommand()).messages
        self.assertEqual(3, len(m))
        self.assertEqual('c1', self.state.character)
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], PhotoAlbumCommand)

    def test_time_ticks(self):
        d = datetime.datetime.now()
        m = self.proc.debug_and_stop_by_empty_queue(TickEvent(d)).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TickEvent(d+datetime.timedelta(seconds=1))).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TickEvent(d+datetime.timedelta(seconds=59))).messages
        self.assertEqual(1, len(m))
        self.assertEqual('a1', self.state.activity)

        m = self.proc.debug_and_stop_by_empty_queue(TickEvent(d+datetime.timedelta(seconds=60))).messages
        self.assertEqual(3, len(m))
        self.assertEqual('a0', self.state.activity)
        self.assertIsInstance(m[1], PhotoAlbumCommand)

        m = self.proc.debug_and_stop_by_empty_queue(TickEvent(d+datetime.timedelta(seconds=120))).messages
        self.assertEqual(3, len(m))
        self.assertEqual('a1', self.state.activity)
        self.assertIsInstance(m[1], PhotoAlbumCommand)

    def test_state_request(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.StateRequest()).messages
        for key, value in self.state.__dict__.items():
            self.assertEqual(value, m[-1].__dict__[key])


class IllustrationSetTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
        records = [
            {'path': f'c0/a0/{index}', 'tags': dict(character='c0', activity='a0', index=index)}
            for index in ('i0', 'i1', 'i2')
        ] + [
            {'path': 'c0/a1/i0', 'tags': dict(character='c0', activity='a1', index='i0')},
        ]
        with zipfile.ZipFile(self.folder/'media_library.zip', 'w') as zp:
            zp.writestr('records.json', json.dumps(records))
        media_library = MediaLibrary.from_folder(self.folder, 'media_library', '.zip')
        content_manager = MediaLibraryManager(media_library, strategy=NewContentStrategy(randomize=False))

        self.proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        self.state = State()
        self.proc.rules.bind(NarrationService(
            self.state,
            SimpleNarrator(content_manager, randomize=False),
            time_between_updates_in_seconds=60,
        ))

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def test_illustration_set_contains_all_siblings_for_the_picked_activity(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand()).messages
        self.assertEqual('a0', self.state.activity)
        illustrations = m[1]
        self.assertIsInstance(illustrations, PhotoAlbumCommand)
        paths = sorted(r.path for r in illustrations.records)
        self.assertEqual(['c0/a0/i0', 'c0/a0/i1', 'c0/a0/i2'], paths)


class SpecialDayExclusionTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()
        records = [
            {'path': 'c0/a0/regular', 'tags': dict(character='c0', activity='a0')},
            {'path': 'c0/a0/halloween', 'tags': dict(character='c0', activity='a0', special_day='Halloween')},
            {'path': 'c0/a1/halloween_only', 'tags': dict(character='c0', activity='a1', special_day='Halloween')},
        ]
        with zipfile.ZipFile(self.folder/'media_library.zip', 'w') as zp:
            zp.writestr('records.json', json.dumps(records))
        media_library = MediaLibrary.from_folder(self.folder, 'media_library', '.zip')
        content_manager = MediaLibraryManager(media_library, strategy=NewContentStrategy(randomize=False))

        self.proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
        self.state = State()
        self.proc.rules.bind(NarrationService(
            self.state,
            SimpleNarrator(content_manager, randomize=False),
            time_between_updates_in_seconds=60,
        ))

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def test_special_day_records_are_never_added_to_the_photo_album(self):
        m = self.proc.debug_and_stop_by_empty_queue(NarrationService.ChangeCharacterCommand()).messages
        self.assertEqual('a0', self.state.activity)
        illustrations = m[1]
        self.assertIsInstance(illustrations, PhotoAlbumCommand)
        paths = sorted(r.path for r in illustrations.records)
        self.assertEqual(['c0/a0/regular'], paths)
