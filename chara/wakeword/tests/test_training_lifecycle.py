import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chara.wakeword.generation.io import sha256
from chara.wakeword.training.pipeline import run_training
from chara.wakeword.training.settings import TrainingSettings
from chara.wakeword.training.state import run_lock
from training_fixtures import dataset_fixture


class LifecycleTests(unittest.TestCase):
    def test_concurrent_lock(self):
        with tempfile.TemporaryDirectory() as tmp, run_lock(tmp):  # noqa: SIM117 - Keep acquisition separate from the expected failure scope.
            with self.assertRaises(RuntimeError):
                with run_lock(tmp):
                    pass

    def test_changed_settings_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            self.assertEqual(
                run_training(data, TrainingSettings(), output).status, "complete"
            )
            original = sha256(output / "state.json")
            result = run_training(data, TrainingSettings(seed=43), output)
            self.assertIn("changed", result.error)
            self.assertEqual(original, sha256(output / "state.json"))

    def test_cache_recovery_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            settings = TrainingSettings()
            result = run_training(data, settings, output)
            self.assertEqual(result.status, "complete", result.error)
            before = sha256(output / "history.jsonl")
            result.report.unlink()
            with patch(
                "chara.wakeword.training.trainer.train",
                side_effect=AssertionError("no retrain"),
            ):
                result = run_training(data, settings, output)
            self.assertEqual(result.status, "complete", result.error)
            self.assertEqual(before, sha256(output / "history.jsonl"))
            result.model.write_bytes(b"broken")
            self.assertEqual(run_training(data, settings, output).status, "failed")

    def test_late_failure_reuses_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            with patch(
                "chara.wakeword.training.checkpoints.select_state",
                side_effect=RuntimeError("injected selection fault"),
            ):
                result = run_training(data, TrainingSettings(), output)
            self.assertEqual(result.error_stage, "selecting")
            before = sha256(output / "history.jsonl")
            with patch(
                "chara.wakeword.training.trainer.train",
                side_effect=AssertionError("no retrain"),
            ):
                result = run_training(data, TrainingSettings(), output)
            self.assertEqual(result.status, "complete", result.error)
            self.assertEqual(before, sha256(output / "history.jsonl"))

    def test_partial_training_requires_new_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            with patch(
                "chara.wakeword.training.trainer.train",
                side_effect=KeyboardInterrupt("injected"),
            ):
                self.assertEqual(
                    run_training(data, TrainingSettings(), output).status, "failed"
                )
            result = run_training(data, TrainingSettings(), output)
            self.assertIn("new output folder", result.error)
            self.assertEqual(
                run_training(data, TrainingSettings(), root / "new").status, "complete"
            )

    def test_other_late_failures(self):
        for target, stage in [
            ("export.export_model", "exporting"),
            ("validation.evaluate", "evaluating"),
            ("reporting.write_report", "reporting"),
        ]:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                data = dataset_fixture(root / "source")
                output = root / "out"
                with patch(
                    "chara.wakeword.training." + target,
                    side_effect=RuntimeError("injected " + stage),
                ):
                    result = run_training(data, TrainingSettings(), output)
                self.assertEqual(result.error_stage, stage)
                before = sha256(output / "history.jsonl")
                with patch(
                    "chara.wakeword.training.trainer.train",
                    side_effect=AssertionError("no updates"),
                ):
                    result = run_training(data, TrainingSettings(), output)
                self.assertEqual(result.status, "complete", result.error)
                self.assertEqual(before, sha256(output / "history.jsonl"))
