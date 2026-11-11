import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
    def run_stage(self, mode):
        jobs = {}
        calls = []

        class Jobs:
            def get_job(self, task_id):
                if mode == "unavailable":
                    raise ConnectionError("offline")
                if task_id not in jobs:
                    raise ValueError("Can't find a job with id " + task_id)
                return jobs[task_id]

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
            api = SimpleNamespace(jobs=Jobs())
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
