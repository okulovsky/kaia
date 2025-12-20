import os

from chara.common import MultifileCache, logger
from unittest import TestCase
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

class FileCacheTestCase(TestCase):
    def test_file_cache(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            cache = MultifileCache()
            cache.initialize(folder)

            @logger.phase(cache)
            def _():
                with cache.session():
                    cache.write(dict(a=1))
                    cache.write(dict(a=2))

            result = cache.read().to_list()
            self.assertEqual([{'a': 1}, {'a': 2}], result)
            self.assertEqual(dict(records=2), FileIO.read_json(folder/'counts.json'))

            @logger.phase(cache)
            def _():
                self.fail("Should not enter the second time")

    def test_exception(self):
        with Loc.create_test_folder() as folder:
            cache = MultifileCache()
            cache.initialize(folder)
            with self.assertRaises(Exception):
                with cache.session():
                    cache.write(dict(a=1))
                    raise Exception()
            self.assertFalse(cache.ready)



