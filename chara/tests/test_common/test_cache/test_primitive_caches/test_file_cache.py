from chara.common import FileCache, logger
from unittest import TestCase
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

class FileCacheTestCase(TestCase):
    def test_file_cache(self):
        with Loc.create_test_folder() as folder:
            item = FileCache()
            item.initialize(folder)

            @logger.phase(item)
            def _():
                item.write('TEST')

            self.assertTrue("TEST", item.read())
            self.assertTrue("TEST", FileIO.read_pickle(item.cache_file_path))

            @logger.phase(item)
            def _():
                self.fail("Should not entered the second time")