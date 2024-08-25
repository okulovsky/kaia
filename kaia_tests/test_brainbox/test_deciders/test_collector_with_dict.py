from kaia.brainbox import IDecider, BrainBoxTask, BrainBoxTaskPack, BrainBoxTestApi
from kaia.brainbox.deciders import Collector
from unittest import TestCase

class TestDecider(IDecider):
    def __call__(self, name, value):
        return {name:value}

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass


class CollectDictTestCase(TestCase):
    def test_collector_to_array(self):
        builder = Collector.PackBuilder()
        builder.append(BrainBoxTask.call(TestDecider)(name='a', value=1).to_task(), dict(tag=1))
        builder.append(BrainBoxTask.call(TestDecider)(name='b', value=2), dict(tag=2))
        pack = builder.to_collector_pack('to_array')
        services = dict(TestDecider=TestDecider(), Collector=Collector())
        with BrainBoxTestApi(services) as api:
            result = api.execute(pack)
            self.assertListEqual(
                [{'tags': {'tag': 1}, 'result': {'a': 1}, 'error': None},
                 {'tags': {'tag': 2}, 'result': {'b': 2}, 'error': None}],
                result
            )


    def test_collector_to_dict(self):
        pack = BrainBoxTaskPack(
            BrainBoxTask(decider=Collector.to_dict, dependencies=dict(A='test-a', B='test-b')),
            (
                BrainBoxTask(decider=TestDecider, arguments=dict(name='a', value=1), id='test-a'),
                BrainBoxTask(decider=TestDecider, arguments=dict(name='b', value=2), id='test-b')
            )
        )
        services = dict(TestDecider=TestDecider(), Collector=Collector())
        with BrainBoxTestApi(services) as api:
            result = api.execute(pack)
        self.assertDictEqual(
            dict(A=dict(a=1), B=dict(b=2)),
            result
        )


