from brainbox.deciders import Empty, Collector
from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from yo_fluq import Query

class PackTestCase(TestCase):
    def test_pack(self):
        with BrainBoxApi.Test() as api:
            builder = Collector.TaskBuilder()
            for tags in Query.combinatorics.grid(a=list(range(3)), b=list(range(2))):
                builder.append(
                    BrainBoxTask.call(Empty)(a=tags.a, b=tags.b),
                    tags
                )
            pack = builder.to_collector_pack('to_array')
            result = api.execute(pack)
            tags = list(sorted((z['tags']['a'], z['tags']['b']) for z in result))
            self.assertEqual(
                [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                tags
            )
            for record in result:
                self.assertDictEqual(record['tags'], record['result'])
