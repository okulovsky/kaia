import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chara.wakeword.training.full_pipeline import run_full
from chara.wakeword.training.settings import TrainingSettings
from training_fixtures import dataset_fixture


class FullTests(unittest.TestCase):
    def test_external_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            with patch(
                "chara.wakeword.generation.pipeline.run",
                side_effect=AssertionError("no generation"),
            ):
                result = run_full(None, TrainingSettings(), root / "full", dataset=data)
                self.assertEqual(result.status, "complete", result.error)
                self.assertTrue((root / "full/full-run.json").exists())
                self.assertFalse((root / "full/generation").exists())

    def test_make_arguments_and_invalid_cli(self):
        from chara.wakeword.scripts.manage import main

        with self.assertRaises(SystemExit) as error:
            main(["train", "--output", "out"])
        self.assertEqual(error.exception.code, 2)
        with (
            patch("chara.wakeword.scripts.manage._training_preflight") as preflight,
            patch(
                "chara.wakeword.scripts.manage._generation",
                side_effect=AssertionError("no brainbox"),
            ),
        ):
            self.assertEqual(
                main(["check", "--scope", "full", "--dataset", "folder with spaces"]), 0
            )
            preflight.assert_called_once()
