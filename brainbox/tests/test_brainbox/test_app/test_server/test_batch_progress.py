from unittest import TestCase
from brainbox.framework import IDecider, BrainBoxTask, BrainBoxApi, BrainBoxCombinedTask
from brainbox.deciders import Collector

class TestDecider(IDecider):
    def run(self, arg):
        return f"OK-{arg}"



class BrainBoxWebServerEmptyTestCase(TestCase):
    def test_all_kinds_of_data(self):
        with BrainBoxApi.Test([TestDecider(), Collector()]) as api:

            builder = Collector.TaskBuilder()
            for i in range(5):
                builder.append(
                    BrainBoxTask(
                        id=f'test-{i}',
                        decider='TestDecider',
                        decider_method='run',
                        arguments=dict(arg=i)),
                    dict(index=i)
                )
            task = builder.to_collector_pack('to_array')

            id = api.add(task)
            result = api.batch_progress(id)
            self.assertIn('progress', result)
            self.assertIsInstance(result['progress'], float)
            api.join(id)
            result = api.batch_progress(id)
            self.assertEqual(1, result['progress'])

