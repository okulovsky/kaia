import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
try:
    from chara import CaseCollection
    from wakeword.generation import brainbox_execution as execution
    from wakeword.generation.dto import AudioCase
except ImportError:
    execution = None


@unittest.skipIf(execution is None, "requires the kaia environment")
class DurableExecutionTests(unittest.TestCase):
    def test_submits_whole_party_once(self):
        api = SimpleNamespace(jobs=Mock())
        descriptions = [SimpleNamespace(id=str(i)) for i in range(50)]
        execution.DurableCasePipeline._submit_missing(api, descriptions)
        api.jobs.base_add.assert_called_once_with(descriptions)

    def test_bulk_results_are_mapped_by_id_after_progress(self):
        jobs = Mock()
        jobs.get_jobs.return_value = [
            SimpleNamespace(id="b", finished=True, error="failed"),
            SimpleNamespace(id="a", finished=True, error=None),
        ]
        batches = Mock()
        batches.get_batch_progress.side_effect = [
            SimpleNamespace(is_finished=False),
            SimpleNamespace(is_finished=True),
        ]
        api = SimpleNamespace(jobs=jobs, batches=batches)
        with patch.object(execution.time, "sleep") as sleep:
            result = execution.DurableCasePipeline._wait_for_results(
                api, ["a", "b"], "batch"
            )
        self.assertEqual(result["b"].error, "failed")
        jobs.get_jobs.assert_called_once_with(["a", "b"])
        jobs.get_job.assert_not_called()
        self.assertEqual(batches.get_batch_progress.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_batch_identity_survives_restart_and_differs_between_runs(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            persist = execution.DurableCasePipeline._persist_batch
            first = persist(Path(a), ["a"])
            self.assertEqual(persist(Path(a), ["a"]), first)
            self.assertNotEqual(persist(Path(b), ["a"]), first)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                persist(Path(a), ["other"])

    def test_missing_results_fail_instead_of_publishing(self):
        api = SimpleNamespace(jobs=Mock(), batches=Mock())
        api.jobs.get_jobs.return_value = []
        api.batches.get_batch_progress.return_value = SimpleNamespace(is_finished=True)
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            execution.DurableCasePipeline._wait_for_results(api, ["a"], "batch")

    def test_lost_submission_with_unknown_state_is_not_retried(self):
        api = SimpleNamespace(jobs=Mock())
        api.jobs.base_add.side_effect = ConnectionError("lost response")
        api.jobs.get_jobs.side_effect = ConnectionError("offline")
        with self.assertRaises(ConnectionError):
            execution.DurableCasePipeline._submit_missing(
                api, [SimpleNamespace(id="a")]
            )
        self.assertEqual(api.jobs.base_add.call_count, 1)

    def run_stage(self, mode):
        jobs = {}
        calls = []

        class Jobs:
            def get_job(self, task_id):
                if mode == "unavailable":
                    raise ConnectionError("offline")
                if task_id not in jobs:
                    raise ValueError("Can't find a job with id " + task_id)
                jobs[task_id].id = task_id
                return jobs[task_id]

            def get_jobs(self, ids):
                return [self.get_job(identity) for identity in ids]

            def get_batch_progress(self, batch_id):
                return SimpleNamespace(is_finished=True)

            def base_add(self, descriptions):
                calls.extend(descriptions)
                jobs["stable"] = SimpleNamespace(finished=True, error=None, result=[])
                if mode == "lost_response":
                    raise ConnectionError("response lost after commit")

        if mode == "existing":
            jobs["stable"] = SimpleNamespace(finished=True, error=None, result=[])
        task = SimpleNamespace(
            optionals=SimpleNamespace(id="stable"),
            to_job_request=lambda: SimpleNamespace(
                jobs=[SimpleNamespace(id="stable", dependencies={}, batch=None)]
            ),
        )
        case = AudioCase("sample", "sample", "positive", "train", 42, 0, "computer")
        with tempfile.TemporaryDirectory() as folder:
            service = Jobs()
            api = SimpleNamespace(jobs=service, batches=service)
            chara = SimpleNamespace(
                current=SimpleNamespace(folder=Path(folder)),
                Apis=SimpleNamespace(brainbox_api=api),
            )
            with patch.object(execution, "Chara", chara):
                stage = execution.DurableCasePipeline(lambda c: task, "recognition")
                result = stage(CaseCollection([case]))
                self.assertEqual(result.successes[0].recognition, [])
        return calls

    def test_existing_job_not_resubmitted(self):
        self.assertEqual(self.run_stage("existing"), [])

    def test_lost_response_does_not_duplicate(self):
        self.assertEqual(len(self.run_stage("lost_response")), 1)

    def test_unknown_server_state_refuses_synthesis(self):
        with self.assertRaises(RuntimeError):
            self.run_stage("unavailable")
