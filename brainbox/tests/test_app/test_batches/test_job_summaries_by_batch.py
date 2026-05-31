from unittest import TestCase
from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.brainbox import BrainBox
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.app.serverless_test import ServerlessTest
from brainbox.deciders import Collector


class SimpleDecider(ISelfManagingDecider):
    def run(self, arg=None):
        return f'OK-{arg}'


registry = ControllerRegistry([SimpleDecider(), Collector()])


class TestGetJobSummariesByBatch(TestCase):
    def test_returns_only_jobs_of_requested_batch(self):
        with ServerlessTest(registry=registry) as api:
            id1 = api.add(BrainBox.TaskBuilder.call(SimpleDecider, id='t1').run('A'))
            id2 = api.add(BrainBox.TaskBuilder.call(SimpleDecider, id='t2').run('B'))
            api.join([id1, id2])

            summaries1 = api.batches.get_job_summaries_by_batch(id1)
            summaries2 = api.batches.get_job_summaries_by_batch(id2)

            self.assertEqual(1, len(summaries1))
            self.assertEqual('t1', summaries1[0].id)
            self.assertEqual(1, len(summaries2))
            self.assertEqual('t2', summaries2[0].id)

    def test_summary_fields_are_correct(self):
        with ServerlessTest(registry=registry) as api:
            id = api.add(BrainBox.TaskBuilder.call(SimpleDecider, id='t1').run('hello'))
            api.join(id)

            summaries = api.batches.get_job_summaries_by_batch(id)
            self.assertEqual(1, len(summaries))
            s = summaries[0]
            self.assertEqual('t1', s.id)
            self.assertEqual('SimpleDecider', s.decider)
            self.assertTrue(s.finished)
            self.assertIsNotNone(s.finished_timestamp)
            self.assertIsNotNone(s.accepted_timestamp)

    def test_ordering_oldest_first(self):
        with ServerlessTest(registry=registry) as api:
            builder = Collector.TaskBuilder()
            for i in range(3):
                builder.append(BrainBox.TaskBuilder.call(SimpleDecider, id=f'leaf{i}').run(i))
            batch_id = api.add(builder.to_collector_pack('to_array'))
            api.join(batch_id)

            summaries = api.batches.get_job_summaries_by_batch(batch_id)
            timestamps = [s.received_timestamp for s in summaries]
            self.assertEqual(timestamps, sorted(timestamps))
