import time

from brainbox import BrainBox
from unittest import TestCase
from brainbox.deciders import Collector, FakeText
from yo_fluq import Query

def generate_pack() -> BrainBox.CombinedTask:
    builder = Collector.TaskBuilder()
    for i in range(5):
        builder.append(
            BrainBox.Task.call(FakeText)(prefix=str(i), time_to_sleep=0.1),
            {}
        )
    return builder.to_collector_pack('to_array')



class CancelTestCase(TestCase):
    def test_cancel_batch(self):
        with BrainBox.Api.Test() as api:
            pack = generate_pack()
            id = pack.resulting_task.get_resulting_id()
            api.add(pack)
            time.sleep(0.3)
            api.cancel(batch_id=id)
            summary = api.summary(batch_id=id)

            try:
                self.assertTrue(summary[0]['success'])
                self.assertTrue(summary[-2]['finished'])
                self.assertFalse(summary[-2]['success'])
                self.assertEqual('Cancelled', summary[-2]['error'])
            except:
                print(summary)
                raise

    def test_cancel_task(self):
        with BrainBox.Api.Test() as api:
            pack = generate_pack()
            id = pack.intermediate_tasks[-1].get_resulting_id()
            batch_id = pack.resulting_task.get_resulting_id()
            api.add(pack)
            api.cancel(job_id=id)
            result = api.join(batch_id)
            for r in result:
                if r['tags'] != 4:
                    self.assertIsNotNone(r['result'])
                    self.assertIsNone(r['error'])
                else:
                    self.assertIsNone(r['result'])
                    self.assertEquals('Cancelled', r['error'])
