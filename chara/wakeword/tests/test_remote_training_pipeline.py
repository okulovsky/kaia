"""Remote orchestration uses cache uploads rather than host filesystem arguments."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
    TrainingSettings,
)
from chara.wakeword.training_pipeline import TrainingPipeline


class RemotePipelineTests(unittest.TestCase):
    def test_dataset_is_uploaded_before_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pipeline = TrainingPipeline(root, TrainingSettings(), {}, root / "output")
            pipeline.output.mkdir()
            pipeline.request = {"task_id": "stable", "training_id": "run"}
            pipeline.manifest = {"corpus_id": "expected-corpus"}
            pipeline.archive = root / "dataset.zip"
            pipeline.archive.write_bytes(b"fixture")
            pipeline.api = SimpleNamespace(jobs=Mock(), cache=Mock(), add=Mock())
            pipeline.api.jobs.get_job.side_effect = [
                ValueError("Can't find a job with id stable"),
                ValueError("Can't find a job with id stable"),
            ]
            with patch(
                "chara.wakeword.training.submission.Submission.follow",
                return_value={"status": "complete"},
            ):
                pipeline._train()
            pipeline.api.cache.upload.assert_called_once_with(
                "wakeword-dataset.stable.zip", pipeline.archive
            )
            task = pipeline.api.add.call_args.args[0].to_job_request().jobs[0]
            self.assertEqual(task.arguments["dataset"], "wakeword-dataset.stable.zip")
            self.assertEqual(
                task.arguments["expected_dataset"]["corpus_id"], "expected-corpus"
            )

    def test_invalid_dataset_fails_before_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pipeline = TrainingPipeline(
                root / "missing", TrainingSettings(), {}, root / "output"
            )
            with patch.object(pipeline, "_check_remote") as remote:
                with self.assertRaises(FileNotFoundError):
                    pipeline()
                remote.assert_not_called()

    def test_expired_cache_reexports_without_training(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pipeline = TrainingPipeline(root, TrainingSettings(), {}, root)
            pipeline.request = {"export_task_id": "old", "export_cache_name": "expired"}
            pipeline.api = SimpleNamespace(
                cache=SimpleNamespace(is_file=lambda name: False)
            )
            with (
                patch.object(pipeline, "_export", return_value="fresh") as export,
                patch.object(
                    pipeline, "_train", side_effect=AssertionError("no updates")
                ),
                patch(
                    "chara.wakeword.training.results.download",
                    return_value="received",
                ) as download,
            ):
                self.assertEqual(
                    pipeline._download("expired", {"status": "complete"}), "received"
                )
                export.assert_called_once()
                self.assertEqual(download.call_args.args[1], "fresh")
            self.assertNotEqual(pipeline.request["export_task_id"], "old")
