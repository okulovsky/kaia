import tempfile
import unittest
from pathlib import Path

from chara.wakeword.generation.io import sha256
from chara.wakeword.training.pipeline import run_training
from chara.wakeword.training.reporting import render_training_report
from chara.wakeword.training.settings import TrainingSettings
from training_fixtures import dataset_fixture


class ReportTests(unittest.TestCase):
    def test_offline_report_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            result = run_training(data, TrainingSettings(), output)
            self.assertEqual(result.status, "complete", result.error)
            text = result.report.read_text(encoding="utf-8")
            self.assertLess(
                text.index('id="validation_metrics"'),
                text.index('id="training_history"'),
            )
            self.assertLess(
                text.index('id="training_history"'),
                text.index('id="dataset_description"'),
            )
            self.assertIn("<svg", text)
            before = sha256(output / "history.jsonl")
            result.report.unlink()
            render_training_report(output)
            self.assertEqual(before, sha256(output / "history.jsonl"))
