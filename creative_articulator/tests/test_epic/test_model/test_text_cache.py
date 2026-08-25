import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from creative_articulator.common import FileNodeStorage
from creative_articulator.epic.model import Paragraph, ParagraphArray, ParagraphType, TextCache


class TestTextCacheParagraphsStaysAParagraphArray(unittest.TestCase):
    def test_direct_construction_with_a_plain_list_is_upgraded(self):
        cache = TextCache([Paragraph('hello', ParagraphType.Plain)], datetime.now())
        self.assertIsInstance(cache.paragraphs, ParagraphArray)
        self.assertTrue(cache.paragraphs.has_type(ParagraphType.Plain))

    def test_survives_a_cache_disk_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = FileNodeStorage(Path(tmp))
            original = TextCache(ParagraphArray(Paragraph('  a plan line', ParagraphType.Plan)), datetime.now())
            storage.set(TextCache, original)

            # A fresh FileNodeStorage forces a real read from disk, rather
            # than returning the in-memory value set above.
            reloaded = FileNodeStorage(Path(tmp)).get(TextCache)

            self.assertIsInstance(reloaded.paragraphs, ParagraphArray)
            self.assertTrue(reloaded.paragraphs.has_type(ParagraphType.Plan))
            self.assertFalse(reloaded.paragraphs.has_type(ParagraphType.Dialog))


if __name__ == '__main__':
    unittest.main()
