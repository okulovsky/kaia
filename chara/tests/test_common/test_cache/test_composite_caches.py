import shutil
from unittest import TestCase
from chara.common import *
from foundation_kaia.misc import Loc
from pathlib import Path


class T(ICache):
    def __init__(self):
        super().__init__()
        self.file_1 = FileCache()
        self.file_2 = FileCache()


class CompositeCacheTest(TestCase):
    def test_composite_cache(self):
        cache = T()
        with Loc.create_test_folder() as folder:

            cache.initialize(folder)
            self.assertEqual(folder/'00_file_1/cache', cache.file_1.cache_file_path)
            self.assertEqual(folder / '01_file_2/cache', cache.file_2.cache_file_path)


            cache.file_1.write('')
            self.assertTrue(cache.file_1.ready)
            self.assertFalse(cache.file_2.ready)

            cache.initialize(folder)
            self.assertTrue(cache.file_1.ready)
            self.assertFalse(cache.file_2.ready)

    def test_composite_cache_consistency(self):
        cache = T()
        with Loc.create_test_folder() as folder:
            cache.initialize(folder)
            cache.file_2.write('')
            self.assertFalse(cache.file_1.ready)
            self.assertTrue(cache.file_2.ready)

            cache.initialize(folder)
            self.assertFalse(cache.file_1.ready)
            self.assertFalse(cache.file_2.ready)

    def test_nested_cache(self):
        class M(ICache):
            def __init__(self):
                super().__init__()
                self.file = FileCache()
                self.composite = T()

        with Loc.create_test_folder() as folder:
            folder = Path(__file__).parent/'test_composite_cache_cache'
            shutil.rmtree(folder, ignore_errors=True)

            cache = M().initialize(folder)
            self.assertEqual(folder/'00_file/cache', cache.file.cache_file_path)
            self.assertEqual(folder/'01_composite/00_file_1/cache', cache.composite.file_1.cache_file_path)














