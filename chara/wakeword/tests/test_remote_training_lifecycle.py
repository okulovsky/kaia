"""A lost HTTP response must never create a second training task."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from chara.wakeword.training.submission import Submission


class SubmissionTests(unittest.TestCase):
    def test_lost_response_reconciles_same_task(self):
        api = SimpleNamespace(
            jobs=Mock(), add=Mock(side_effect=ConnectionError("lost response"))
        )
        api.jobs.get_job.side_effect = [
            ValueError("Can't find a job with id stable"),
            SimpleNamespace(finished=False),
        ]
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(
                Submission(api, Path(folder)).submit("task", "stable"), "stable"
            )
        api.add.assert_called_once_with("task")
        self.assertEqual(api.jobs.get_job.call_args_list[1].args, ("stable",))

    def test_transport_failure_does_not_resubmit(self):
        api = SimpleNamespace(jobs=Mock(), add=Mock())
        api.jobs.get_job.side_effect = ConnectionError("offline")
        with (
            tempfile.TemporaryDirectory() as folder,
            self.assertRaisesRegex(RuntimeError, "transport_unknown"),
        ):
            Submission(api, Path(folder)).submit("task", "stable")
        api.add.assert_not_called()

    def test_server_timeout_propagates(self):
        from brainbox.deciders.voice_analysis.wakeword_training.app.training_process import (
            TrainingProcess,
        )

        runtime = SimpleNamespace(
            train=Mock(side_effect=TimeoutError("computation failed")), describe=Mock()
        )
        with self.assertRaisesRegex(TimeoutError, "computation failed"):
            list(TrainingProcess(runtime).run("id", {}, {}, Path("dataset")))
