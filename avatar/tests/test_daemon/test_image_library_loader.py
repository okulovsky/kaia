import json
from unittest import TestCase
from foundation_kaia.misc import Loc
from foundation_kaia.marshalling import Storage
from avatar.daemon.image_service import ImageLibraryLoader
from .media_library_fixture import write_media_library

MAIN = {'file_id': 'main.png', 'tags': {'character': 'c0'}, 'image_fingerprint': {'x': 1}}
VARIANT = {'file_id': 'main-goth.png', 'variant': {'original': 'main.png', 'variant_type': 'goth'}}


class ImageLibraryLoaderTestCase(TestCase):
    def setUp(self):
        self.folder_holder = Loc.create_test_folder()
        self.folder = self.folder_holder.__enter__()

    def tearDown(self):
        self.folder_holder.__exit__(None, None, None)

    def _loader(self, entries, local: bool = True, **kwargs):
        write_media_library(self.folder, entries, **kwargs)
        return ImageLibraryLoader(Storage(self.folder), self.folder if local else None)

    def test_variants_nest_and_are_not_records(self):
        loader = self._loader([MAIN, VARIANT])
        self.assertEqual(['main.png'], [r.file_id for r in loader.get_records()])
        self.assertEqual(['main-goth.png'], [v.file_id for v in loader.get_records()[0].variants])

    def test_variant_before_its_original_still_nests(self):
        loader = self._loader([VARIANT, MAIN])
        self.assertEqual(1, len(loader.get_record('main.png').variants))

    def test_variant_in_another_library_still_nests(self):
        write_media_library(self.folder, [MAIN], name='media_library-1.zip')
        write_media_library(self.folder, [VARIANT], name='media_library-0.zip')
        loader = ImageLibraryLoader(Storage(self.folder), self.folder)
        self.assertEqual(1, len(loader.get_record('main.png').variants))

    def test_variant_without_an_original_is_dropped(self):
        loader = self._loader([VARIANT])
        self.assertEqual([], loader.get_records())

    def test_get_variants_filters_by_type(self):
        loader = self._loader([MAIN, VARIANT])
        self.assertEqual(1, len(loader.get_variants('main.png', 'goth')))
        self.assertEqual([], loader.get_variants('main.png', 'smile'))
        self.assertEqual([], loader.get_variants('unknown.png', 'goth'))

    def test_description_and_tags_are_kept(self):
        loader = self._loader([MAIN])
        record = loader.get_record('main.png')
        self.assertEqual({'character': 'c0'}, record.tags)
        self.assertEqual({'x': 1}, record.description['image_fingerprint'])

    def test_entry_without_tags_gets_an_empty_dict(self):
        loader = self._loader([{'file_id': 'main.png'}])
        self.assertEqual({}, loader.get_record('main.png').tags)

    def test_local_record_reads_its_content(self):
        loader = self._loader([MAIN])
        self.assertEqual(b'image-bytes', loader.get_record('main.png').get_content())

    def test_remote_record_raises_on_get_content(self):
        loader = self._loader([MAIN, VARIANT], local=False)
        record = loader.get_record('main.png')
        self.assertIsNone(record.zip_path)
        with self.assertRaises(ValueError):
            record.get_content()
        with self.assertRaises(ValueError):
            record.variants[0].get_content()

    def test_zips_without_a_description_are_invisible(self):
        (self.folder/'media_library-old.zip').write_bytes(b'not a description')
        loader = self._loader([MAIN])
        self.assertEqual(['main.png'], [r.file_id for r in loader.get_records()])

    def test_feedback_storage_points_at_the_same_folder(self):
        loader = self._loader([MAIN])
        loader.feedback_storage.append('main.png', {'seen': 1})
        self.assertEqual(
            {'main.png': {'seen': 1}},
            json.loads((self.folder/'images-feedback.json').read_text()),
        )
