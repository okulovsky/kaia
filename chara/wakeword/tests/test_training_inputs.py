import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from chara.wakeword.generation.io import read_json, sha256, write_json
from chara.wakeword.training.inputs import resolve_inputs
from chara.wakeword.training.settings import TrainingSettings
from training_fixtures import dataset_fixture


class InputTests(unittest.TestCase):
    def test_settings(self):
        for overrides in [
            {"stage_steps": [1, 2]},
            {"stage_steps": [True, 2, 3]},
            {"threshold": float("nan")},
            {"seed": -1},
            {"model_name": "../x"},
            {"validation_start_fractions": [0, 0, 2]},
        ]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                TrainingSettings(**overrides).validate()

    def test_snapshot_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = dataset_fixture(Path(tmp) / "source")
            snapshot, arrays = resolve_inputs(root)
            self.assertEqual(snapshot["background"]["total_valid_windows"], 10)
            self.assertEqual(snapshot["background"]["evaluated_frames"], 40)
            self.assertIsInstance(arrays["positive_features_train"], np.memmap)
            for array in arrays.values():
                array._mmap.close()
            with (root / "dataset/positive_features_train.npy").open("ab") as f:
                f.write(b"broken")
            with self.assertRaisesRegex(ValueError, "hash"):
                resolve_inputs(root)

    def test_no_bare_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:  # noqa: SIM117 - Keep acquisition separate from the expected failure scope.
            with self.assertRaises((ValueError, FileNotFoundError)):
                resolve_inputs(tmp)

    def test_invalid_arrays_before_training(self):
        for value in [
            np.empty((0, 16, 96)),
            np.zeros((1, 15, 96)),
            np.full((1, 16, 96), np.nan),
            np.full((1, 16, 96), 1e100),
            np.zeros((1, 16, 96), dtype="complex64"),
        ]:
            with (
                self.subTest(shape=value.shape, dtype=value.dtype),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = dataset_fixture(Path(tmp) / "source")
                manifest_path = root / "dataset/manifest.json"
                m = read_json(manifest_path)
                name = "positive_features_train"
                path = root / "dataset" / m["artifacts"][name]["path"]
                np.save(path, value)
                m["artifacts"][name].update(
                    sha256=sha256(path), shape=list(value.shape), dtype=str(value.dtype)
                )
                write_json(manifest_path, m)
                with self.assertRaises(ValueError):
                    resolve_inputs(root)

    def test_cross_split_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = dataset_fixture(Path(tmp) / "source")
            path = root / "dataset/manifest.json"
            m = read_json(path)
            m["lineage"] = [
                {"lineage_id": "same", "split": s} for s in ("train", "test")
            ]
            write_json(path, m)
            with self.assertRaisesRegex(ValueError, "lineage"):
                resolve_inputs(root)

    def test_finite_scan_is_bounded_for_fortran_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = dataset_fixture(Path(tmp) / "source")
            path = root / "dataset/positive_features_train.npy"
            value = np.asfortranarray(np.zeros((512, 16, 96), dtype="float32"))
            np.save(path, value)
            manifest_path = root / "dataset/manifest.json"
            m = read_json(manifest_path)
            m["artifacts"]["positive_features_train"].update(
                sha256=sha256(path), shape=list(value.shape)
            )
            write_json(manifest_path, m)
            sizes = []
            finite = np.isfinite

            def checked(x):
                sizes.append(np.size(x))
                return finite(x)

            with patch(
                "chara.wakeword.training.inputs.np.isfinite", side_effect=checked
            ):
                _, arrays = resolve_inputs(root)
            try:
                self.assertLessEqual(max(sizes), 262144)
                self.assertIsInstance(arrays["positive_features_train"], np.memmap)
            finally:
                for a in arrays.values():
                    a._mmap.close()
