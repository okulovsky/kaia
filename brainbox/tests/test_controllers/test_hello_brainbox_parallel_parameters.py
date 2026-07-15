from unittest import TestCase
from brainbox.framework import BrainBoxApi
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox


def _interval(summaries):
    starts = [s.accepted_timestamp for s in summaries]
    ends = [s.finished_timestamp for s in summaries]
    return min(starts), max(ends)


def _intervals_intersect(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    return start1 <= end2 and start2 <= end1


class HelloBrainBoxParallelParametersTestCase(TestCase):
    def test_two_parameters_run_concurrently(self):
        with BrainBoxApi.test(
            [HelloBrainBox.Controller()],
            default_resources_folder=False,
            always_on_planner=True,
        ) as api:
            a_tasks = [HelloBrainBox.new_task(parameter='A').parameter() for _ in range(10)]
            b_tasks = [HelloBrainBox.new_task(parameter='B').parameter() for _ in range(10)]

            # Submit both series in one batch, so both containers get started and
            # their tasks get processed concurrently rather than one after another.
            all_ids = api.add(a_tasks + b_tasks)
            a_ids, b_ids = all_ids[:10], all_ids[10:]

            all_results = api.join(all_ids)
            a_results, b_results = all_results[:10], all_results[10:]

            self.assertEqual(['A'] * 10, a_results)
            self.assertEqual(['B'] * 10, b_results)

            a_interval = _interval(api.jobs.get_job_summaries(a_ids))
            b_interval = _interval(api.jobs.get_job_summaries(b_ids))
            self.assertTrue(
                _intervals_intersect(a_interval, b_interval),
                f"Expected the A-series interval {a_interval} and the B-series interval {b_interval} "
                f"to overlap, proving both parameter instances ran concurrently."
            )

            status = api.controllers.status()
            controller_status = next(c for c in status.controllers if c.name == 'HelloBrainBox')
            self.assertEqual(2, len(controller_status.instances))
            self.assertEqual({'A', 'B'}, {i.parameter for i in controller_status.instances})
