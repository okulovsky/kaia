from unittest import TestCase
from brainbox.framework import ISelfManagingDecider, BrainBox
from datetime import datetime
from tqdm import tqdm


class EmptyDecider(ISelfManagingDecider):
    def run(self):
        return "OK"

class LatencyTestCase(TestCase):
    def test_latency(self):
        with BrainBox.Api.test([EmptyDecider()]) as api:
            api.execute(BrainBox.TaskBuilder.call(EmptyDecider).run())
            rows = {}
            N=10
            for i in tqdm(range(N), total=N):
                task = BrainBox.TaskBuilder.call(EmptyDecider).run()
                start_time = datetime.now()
                id = api.add(task)
                result = api.join(id)
                rows[id] = dict(start = start_time, end = datetime.now())

            for id, row in tqdm(rows.items(), total=len(rows)):
                job = api.tasks.get_job(id)
                row['to_server_time'] = (job.received_timestamp - row['start']).total_seconds()
                row['in_queue_time'] = (job.accepted_timestamp - job.received_timestamp).total_seconds()
                row['in_operator_time'] = (job.finished_timestamp - job.accepted_timestamp).total_seconds()
                row['from_server_time'] = (row['end'] - job.finished_timestamp).total_seconds()
                row['total_time'] = (row['end'] - row['start']).total_seconds()

            for key in rows[list(rows)[0]]:
                if key.endswith('_time'):
                    print(f"{key}: {sum(row[key] for row in rows.values())/len(rows)}")







