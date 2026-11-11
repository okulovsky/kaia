import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chara.wakeword.generation.io import read_json, write_json
from chara.wakeword.training.pipeline import run_training
from chara.wakeword.training.reporting import render_training_report
from chara.wakeword.training.settings import TrainingSettings
from training_fixtures import dataset_fixture


class ConsistencyTests(unittest.TestCase):
    def test_no_inference_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            result = run_training(data, TrainingSettings(), output)
            self.assertEqual(result.status, "complete", result.error)
            with (
                patch(
                    "onnxruntime.InferenceSession",
                    side_effect=AssertionError("no inference"),
                ),
                patch("torch.optim.Adam", side_effect=AssertionError("no training")),
            ):
                self.assertTrue(render_training_report(output).exists())
            m = read_json(output / "metrics.json")
            m["supervised"]["recall"] = 0.123
            write_json(output / "metrics.json", m)
            with self.assertRaises(ValueError):
                render_training_report(output)
