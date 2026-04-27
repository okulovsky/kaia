#TODO: More of tests on collector are needed, not media-library related

from brainbox.deciders import Collector
from unittest import TestCase
from brainbox.framework import BrainBoxApi, BrainBox, ISelfManagingDecider
from yo_fluq import Query

class Empty(ISelfManagingDecider):
    def run(self, a: int, b: int) -> dict[str,int]:
        return dict(a=a, b=b)

class CollectorTestCase(TestCase):
    def test_pack(self):
        with BrainBoxApi.test([Empty(), Collector()]) as api:
            builder = Collector.TaskBuilder()
            for tags in Query.combinatorics.grid(a=list(range(3)), b=list(range(2))):
                builder.append(
                    BrainBox.TaskBuilder.call(Empty).run(a=tags.a, b=tags.b),
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
