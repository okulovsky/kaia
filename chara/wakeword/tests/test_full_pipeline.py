import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from training_fixtures import dataset_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
    TrainingSettings,
)
from chara.wakeword.training.full_pipeline import run_full


class FullTests(unittest.TestCase):
    def test_external_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            with (
                patch(
                    "chara.wakeword.training.full_pipeline.run_training",
                    return_value=SimpleNamespace(status="complete", error=None),
                ),
                patch(
                    "chara.wakeword.generation_pipeline.run",
                    side_effect=AssertionError("no generation"),
                ),
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
        with patch("chara.wakeword.scripts.common.main", return_value=0) as canonical:
            self.assertEqual(
                main(["check", "--scope", "full", "--dataset", "folder with spaces"]), 0
            )
            canonical.assert_called_once_with(
                "prepare",
                ["--scope", "all", "--dataset", "folder with spaces", "--check-only"],
            )
