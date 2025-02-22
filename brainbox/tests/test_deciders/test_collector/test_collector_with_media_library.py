from numpy.core.records import record
import zipfile
from brainbox.framework import BrainBoxApi, BrainBoxTask, MediaLibrary
from brainbox.deciders import FakeFile, Collector, FakeText
from unittest import TestCase
from yo_fluq import Query
import pickle
import json

class CollectorWithMediaLibraryTestCase(TestCase):
    def test_to_list(self):
        with BrainBoxApi.ServerlessTest([FakeText(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .combinatorics.grid(a=list(range(3)), b=list(range(2)))
                .foreach(lambda z: builder.append(
                    BrainBoxTask.call(FakeText)(f'{z.a}/{z.b}'),
                    z
                )))
            result = api.execute(builder.to_collector_pack('to_array'))
            tags = list(sorted((z['tags']['a'], z['tags']['b']) for z in result))
            self.assertEqual(
                [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                tags
            )
            for record in result:
                self.assertTrue(
                record['result'].startswith(f'{record["tags"]["a"]}/{record["tags"]["b"]}')
            )


    def test_media_library_one_file_returned(self):
        with BrainBoxApi.ServerlessTest([FakeFile(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .en(range(5))
                .select(lambda z: dict(prefix=z))
                .foreach(
                    lambda z: builder.append(
                        BrainBoxTask.call(FakeFile)(z),
                        z
                    )
            ))
            result = api.execute(builder.to_collector_pack('to_media_library'))
            ml = MediaLibrary.read(api.cache_folder/result)
            self.assertEqual(5, len(ml.records))
            for rec in ml.records:
                js = json.loads(rec.get_content())
                self.assertDictEqual(dict(prefix=rec.tags['prefix']), js)


    def test_media_library_several_files_returned(self):
        with BrainBoxApi.ServerlessTest([FakeFile(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .en(range(2))
                .select(lambda z: dict(prefix=z))
                .foreach(lambda z: builder.append(
                    BrainBoxTask.call(FakeFile)(z, array_length=3),
                    z
                )))
            result = api.execute(builder.to_collector_pack('to_media_library'))
            ml = MediaLibrary.read(api.cache_folder/result)
            self.assertEqual(6, len(ml.records))
            tags = list(sorted( (z.tags['prefix'], z.tags['option_index']) for z in ml.records ) )
            self.assertEqual([(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)], tags)

    def test_media_library_inline(self):
        with BrainBoxApi.ServerlessTest([FakeText(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .en(range(2))
                .select(lambda z: dict(prefix=z))
                .foreach(lambda z: builder.append(
                    BrainBoxTask.call(FakeText)(f'prefix{z["prefix"]}'),
                    z
            )))
            result = api.execute(builder.to_collector_pack('to_media_library'))
            ml = MediaLibrary.read(api.cache_folder/result)
            self.assertEqual(2, len(ml.records))
            for rec in ml.records:
                self.assertTrue(rec.inline_content.startswith(f'prefix{rec.tags["prefix"]}'))

    def test_media_library_on_zip_file_level(self):
        with BrainBoxApi.ServerlessTest([FakeFile(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .en(range(5))
                .select(lambda z: dict(prefix=z))
                .foreach(lambda z: builder.append(
                    BrainBoxTask.call(FakeFile)(dict(prefix=z["prefix"])),
                    z
            )))
            result = api.execute(builder.to_collector_pack('to_media_library'))
            with zipfile.ZipFile(api.cache_folder/result,'r') as zip:
                records = pickle.loads(zip.read('description.pkl'))
                self.assertEqual(5, len(records))
                for value in records.values():
                    self.assertIsInstance(value, dict)

    def test_medialibrary_correct_batches_assigned(self):
        with BrainBoxApi.ServerlessTest([FakeFile(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .en(range(5))
                .select(lambda z: dict(prefix=z))
                .foreach(
                    lambda z: builder.append(
                        BrainBoxTask.call(FakeFile)(dict(prefix=z["prefix"])),
                        z
            )))
            api.execute(builder.to_collector_pack('to_media_library'))
            result = api.summary()
            batches = [r['batch'] for r in result]
            self.assertEqual(1, len(set(batches)))
