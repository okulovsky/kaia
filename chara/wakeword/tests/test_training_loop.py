import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from chara.wakeword.training.batches import sample_batch, window_batches
from chara.wakeword.training.inputs import resolve_inputs
from chara.wakeword.training.model import WakewordModel
from chara.wakeword.training.settings import TrainingSettings
from chara.wakeword.training.state import history
from chara.wakeword.training.trainer import learning_rate, train, validation_steps
from training_fixtures import dataset_fixture


class LoopTests(unittest.TestCase):
    def test_segments(self):
        x = np.arange(40 * 96).reshape(40, 96)
        batches = list(window_batches(x, [16, 24], 3))
        windows = np.concatenate(batches)
        self.assertEqual(windows.shape, (10, 16, 96))
        np.testing.assert_equal(windows[1], x[16:32])
        self.assertLessEqual(max(map(len, batches)), 3)

    def test_schedule(self):
        self.assertEqual(validation_steps(4, 1, 20), {3})
        self.assertEqual(validation_steps(4, 0, 20), {0, 1, 2, 3})
        self.assertAlmostEqual(learning_rate(0, 20, 0.1), 0.025)

    def test_sampling_seed(self):
        arrays = {
            k: np.zeros((3, 20 if k == "background_train" else 16, 96))
            for k in (
                "positive_features_train",
                "negative_features_train",
                "background_train",
            )
        }
        a = sample_batch(arrays, TrainingSettings(), np.random.default_rng(1))
        b = sample_batch(arrays, TrainingSettings(), np.random.default_rng(1))
        np.testing.assert_equal(a[0], b[0])
        self.assertEqual(a[1].sum(), 2)

    def test_flush_and_actual_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = dataset_fixture(root / "source")
            out = root / "out"
            out.mkdir()
            snapshot, arrays = resolve_inputs(source)
            settings = TrainingSettings(
                stage_steps=[1, 1, 1], accumulation_examples=999
            )
            try:
                result = train(WakewordModel(), arrays, snapshot, settings, out, "cpu")
                self.assertEqual(result["optimizer_updates"], 3)
                records = history(out)
                self.assertEqual(
                    [x["type"] for x in records],
                    ["update", "validation", "stage_end"] * 3,
                )
                self.assertTrue(
                    all(x["flush_remainder"] for x in records if x["type"] == "update")
                )
            finally:
                for a in arrays.values():
                    a._mmap.close()

    def test_no_retained_examples_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = dataset_fixture(root / "source")
            out = root / "out"
            out.mkdir()
            snapshot, arrays = resolve_inputs(source)
            model = WakewordModel()
            # Force saturated positive predictions; batches contain only positives.
            x = np.zeros((2, 16, 96), dtype="float32")
            y = np.ones(2, dtype="float32")
            with torch.no_grad():
                for p in model.parameters():
                    p.zero_()
                model.layer2.bias.fill_(100)
            try:
                with (
                    patch(
                        "chara.wakeword.training.trainer.sample_batch",
                        return_value=(x, y),
                    ),
                    self.assertRaisesRegex(ValueError, "zero optimizer updates"),
                ):
                    train(
                        model,
                        arrays,
                        snapshot,
                        TrainingSettings(stage_steps=[1, 1, 1]),
                        out,
                        "cpu",
                    )
                self.assertFalse(any(x["type"] == "update" for x in history(out)))
            finally:
                for a in arrays.values():
                    a._mmap.close()
