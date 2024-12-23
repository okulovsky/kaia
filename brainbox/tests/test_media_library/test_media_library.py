import json
import os

from brainbox.framework import MediaLibrary, Loc
from unittest import TestCase
from uuid import uuid4
from yo_fluq_ds import FileIO, Query
from datetime import datetime

def create_library(folder):
    os.makedirs(folder, exist_ok=True)
    src = folder / 'src'
    os.makedirs(src, exist_ok=True)

    for lb in [0, 1]:
        content = []
        for i in range(10 + 2 * lb):
            uid = str(uuid4())
            dt = dict(i=i, lb=lb)
            FileIO.write_json(dt, src / uid)
            content.append(MediaLibrary.Record(
                uid,
                src,
                datetime.now(),
                f'job-{lb}',
                dict(lb=lb, i=i),
            ))
        library = MediaLibrary(tuple(content))
        library.save(folder / f'lb_{lb}.zip')
    return folder


class MediaLibraryTestCase(TestCase):
    def test_read(self):
        with Loc.create_test_folder('tests/medialibrary') as folder:
            create_library(folder)
            for lb in [0,1]:
                lib = MediaLibrary.read(folder/f'lb_{lb}.zip')
                for i, rec in enumerate(lib.records):
                    self.assertDictEqual(dict(i=i, lb=lb), json.loads(rec.get_content()))


    def test_merge_read(self):
        with Loc.create_test_folder('tests/medialibrary') as folder:
            create_library(folder)
            lib = MediaLibrary.read(folder/f'lb_0.zip', folder/f'lb_1.zip')
            for i, rec in enumerate(lib.records):
                self.assertDictEqual(dict(i=rec.tags['i'], lb=rec.tags['lb']), json.loads(rec.get_content()))
            lib.save(folder/'merged.zip')
            lib1 = MediaLibrary.read(folder/'merged.zip')
            for i, rec in enumerate(lib1.records):
                self.assertDictEqual(dict(i=rec.tags['i'], lb=rec.tags['lb']), json.loads(rec.get_content()))

    def test_unpack(self):
        with Loc.create_test_folder('tests/medialibrary') as folder:
            create_library(folder)
            lib = MediaLibrary.read(folder / f'lb_0.zip', folder / f'lb_1.zip')
            ulib = lib.unzip(folder/'unzip')
            for i, rec in enumerate(lib.records):
                self.assertDictEqual(dict(i=rec.tags['i'], lb=rec.tags['lb']), json.loads(rec.get_content()))
                self.assertTrue(folder/'unzip'/rec.filename)


    def test_medialibrary_generation(self):
        with Loc.create_test_file('tests/medialibrary', 'zip') as file:
            tags = Query.combinatorics.grid(A=['a','b'], D=[1, 2]).with_indices().to_dictionary(lambda z: str(z.key), lambda z: z.value)
            MediaLibrary.generate(file, tags)
            lib = MediaLibrary.read(file)
            self.assertEqual(4, len(lib.records))
            self.assertDictEqual({'A':'a', 'D':1}, json.loads(lib.records[0].get_content()))





