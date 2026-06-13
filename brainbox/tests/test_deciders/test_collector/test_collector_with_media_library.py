from brainbox import ISelfManagingDecider
import json
from brainbox.framework import BrainBox, File
from brainbox.framework.app.api import BrainBoxApi
from brainbox.deciders import Collector
from unittest import TestCase
from yo_fluq import Query
import string
import random
import time
from copy import copy

class FakeText(ISelfManagingDecider):
    def run(self, prefix = '', length = 0, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        characters = string.ascii_letters + string.digits + string.punctuation
        if length>0:
            result = prefix+' '+''.join(random.choices(characters, k=length))
        else:
            result = prefix
        return result


class FakeFile(ISelfManagingDecider):
    def run(self, tags: dict=None, extension_with_dot='', array_length: int|None = None, time_to_sleep: float|None = None):
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
        with BrainBoxApi.serverless_test([FakeText(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            (
                Query
                .combinatorics.grid(a=list(range(3)), b=list(range(2)))
                .foreach(lambda z: builder.append(
                    BrainBox.TaskBuilder.call(FakeText).run(f'{z.a}/{z.b}'),
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
