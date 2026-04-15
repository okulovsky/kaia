from unittest import TestCase
from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.brainbox import BrainBox
from brainbox.framework.app.api import BrainBoxApi
from brainbox.deciders import Collector


class TestDecider(ISelfManagingDecider):
    def run(self, arg):
        return f"OK-{arg}"


class BatchProgressTestCase(TestCase):
    def test_batch_progress_endpoint(self):
        with BrainBoxApi.test([TestDecider(), Collector()], port=18193) as api:
            builder = Collector.TaskBuilder()
            for i in range(5):
                builder.append(BrainBox.TaskBuilder.call(TestDecider).run(i))

            task = builder.to_collector_pack('to_array')

            id = api.add(task)
            summary = api.batches.get_batch_progress(id)
            self.assertIsInstance(summary.progress, float)

            api.join(id)
            summary = api.batches.get_batch_progress(id)
            self.assertEqual(1.0, summary.progress)
