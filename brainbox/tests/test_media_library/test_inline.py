from unittest import TestCase
from brainbox.framework import Loc, MediaLibrary
from uuid import uuid4
from datetime import datetime
import json



class InlineMediaLibraryTestCase(TestCase):
    def test_inline_media_library(self):
        with Loc.create_test_file('inline_media_library','zip') as fname:
            tags = [dict(a=1, b=2), dict(b=2, c=4)]
            records = []
            for tag in tags:
                records.append(MediaLibrary.Record(str(uuid4()), None, datetime.now(), 'x', tag, json.dumps(tag)))
            lib = MediaLibrary(tuple(records))
            lib.save(fname)

            lib1 = MediaLibrary.read(fname)
            for r in lib1.records:
                self.assertDictEqual(
                    r.tags,
                    json.loads(r.get_content())
                )



