import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from chara.wakeword.training.export import export_model
from chara.wakeword.training.model import WakewordModel
from chara.wakeword.training.settings import TrainingSettings


class ExportTests(unittest.TestCase):
    def test_real_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = export_model(
                WakewordModel(),
                Path(tmp) / "model.onnx",
                np.zeros((3, 16, 96), dtype="float32"),
                TrainingSettings(),
            )
            self.assertTrue(check["parity_passed"])
            self.assertEqual(check["batch_sizes"], [1, 3])

    def test_failed_parity_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.onnx"
            with (
                patch("chara.wakeword.training.export.np.allclose", return_value=False),
                self.assertRaisesRegex(ValueError, "parity"),
            ):
                export_model(
                    WakewordModel(),
                    path,
                    np.zeros((2, 16, 96), dtype="float32"),
                    TrainingSettings(),
                )
            self.assertFalse(path.exists())

    def test_checker_failure_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.onnx"
            with (
                patch(
                    "onnx.checker.check_model", side_effect=ValueError("broken ONNX")
                ),
                self.assertRaises(ValueError),
            ):
                export_model(
                    WakewordModel(),
                    path,
                    np.zeros((2, 16, 96), dtype="float32"),
                    TrainingSettings(),
                )
            self.assertFalse(path.exists())
