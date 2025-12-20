from chara.common import FolderCache, logger
from unittest import TestCase
from foundation_kaia.misc import Loc
from brainbox import File
from yo_fluq import FileIO

class FolderCacheTestCase(TestCase):
    def test_folder_cache(self):
        with Loc.create_test_folder() as folder:
            cache = FolderCache().initialize(folder)
            @logger.phase(cache)
            def _():
                cache.write(b'123')
                cache.write(File('test', b'321'))
                with Loc.create_test_folder() as tmp:
                    FileIO.write_bytes(b'111', tmp/'test_1')
                    cache.write(tmp/'test_1')
                cache.finalize()

            files = {f.name:f.content for f in cache.read_files()}
            print(list(files))
            self.assertEqual(3, len(files))
            id = [c for c in files if c!='test' and c!='test_1']
            self.assertEqual(1, len(id))
            self.assertEqual(b'123', files[id[0]])
            self.assertEqual(b'321', files['test'])
            self.assertEqual(b'111', files['test_1'])

            @logger.phase(cache)
            def _():
                self.fail("Should not enter the second time")
