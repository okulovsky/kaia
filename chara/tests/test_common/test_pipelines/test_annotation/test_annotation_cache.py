from unittest import TestCase
from chara.common.pipelines.annotation import LabelAnnotationCache
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

class AnnotationCacheTestCase(TestCase):
    def test_annotation_cache(self):
        with Loc.create_test_folder() as folder:
            cache = LabelAnnotationCache()
            cache.initialize(folder)

            cache.skip('id1')
            self.assertTrue(cache.temp_file.exists())
            self.assertEqual('!SKIP id1\n', FileIO.read_text(cache.temp_file))

            cache.add('id2', "X")
            self.assertEqual('!SKIP id1\n#id2: X\n', FileIO.read_text(cache.temp_file))

            status = cache.get_annotation_status()
            self.assertIsNone(status['id1'].value)
            self.assertEqual(status['id1'].skipped_times, 1)

            self.assertEqual(status['id2'].value, 'X')
            self.assertEqual(status['id2'].skipped_times, 0)

            with self.assertRaises(ValueError):
                cache.get_result()

            cache.finish_annotation()
            result = cache.get_result()
            self.assertEqual({'id2': 'X'}, result)



