from brainbox.framework import IDecider
from numpy.core.records import record
import zipfile
from brainbox.framework import BrainBoxApi, BrainBoxTask, MediaLibrary, File
from brainbox.deciders import Collector
from unittest import TestCase
from yo_fluq import Query
import pickle
import json
import string
import random
import time
from copy import copy

class FakeText(IDecider):
    def __call__(self, prefix = '', length = 0, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        characters = string.ascii_letters + string.digits + string.punctuation
        if length>0:
            result = prefix+' '+''.join(random.choices(characters, k=length))
        else:
            result = prefix
        return result


class FakeFile(IDecider):
    def __call__(self, tags: dict=None, extension_with_dot='', array_length: int|None = None, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        if tags is None:
            tags = {}
        if array_length is None:
            return File(self.current_job_id+'.output'+extension_with_dot, json.dumps(tags))
        else:
            result = []
            for i in range(array_length):
                new_tags = copy(tags)
                new_tags['option_index'] = i
                result.append(File(self.current_job_id+'.output.'+str(i)+extension_with_dot, json.dumps(new_tags)))
            return result



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
