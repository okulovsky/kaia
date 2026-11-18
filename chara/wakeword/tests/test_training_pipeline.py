import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from training_fixtures import dataset_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.execution import (
    run_training,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
    TrainingSettings,
)
from chara.wakeword.generation.io import read_json


class PipelineTests(unittest.TestCase):
    def test_real_cpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            with patch(
                "chara.wakeword.generation_pipeline.run",
                side_effect=AssertionError("no generation"),
            ):
                result = run_training(data, TrainingSettings(), root / "out")
            self.assertEqual(result.status, "complete", result.error)
            self.assertTrue(result.model.exists())
            self.assertTrue(result.report.exists())
            self.assertGreater(
                read_json(root / "out/state.json")["optimizer_updates"], 0
            )
