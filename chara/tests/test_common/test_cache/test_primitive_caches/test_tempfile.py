from chara.common import TempfileCache, logger
from unittest import TestCase
from foundation_kaia.misc import Loc

class TempfileCacheTestCase(TestCase):
    def test_tempfile_cache(self):
        with Loc.create_test_folder() as folder:
            cache = TempfileCache().initialize(folder)

            @logger.phase(cache)
            def _():
                cache._update('line 1')
                cache._update('line 2')
                cache.finalize()

            self.assertEqual(['line 1', 'line 2'], list(cache._read()))

            @logger.phase(cache)
            def _():
                raise ValueError("Should not enter the second time")

    def test_must_finalize(self):
        with Loc.create_test_folder() as folder:
            cache = TempfileCache().initialize(folder)

            with self.assertRaises(ValueError):
                @logger.phase(cache)
                def _():
                    cache._update('line 1')
                    cache._update('line 2')


