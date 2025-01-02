from brainbox.deciders import FakeText, Collector
from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from yo_fluq import Query

class PackTestCase(TestCase):
    def test_pack(self):
        with BrainBoxApi.Test() as api:
            pack = (
                Query
                .combinatorics.grid(a=list(range(3)), b=list(range(2)))
                .feed(Collector.FunctionalTaskBuilder(
                    lambda z: BrainBoxTask.call(FakeText)(f'{z.a}/{z.b}'),
                    method='to_array'
                )))
            result = api.execute(pack)
            tags = list(sorted((z['tags']['a'], z['tags']['b']) for z in result))
            self.assertEqual(
                [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                tags
            )
            for record in result:
                self.assertTrue(
                record['result'].startswith(f'{record["tags"]["a"]}/{record["tags"]["b"]}')
            )