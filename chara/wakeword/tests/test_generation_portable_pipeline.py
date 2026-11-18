"""Generation's new entry point packages the existing batching/cropping pipeline."""

import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_pipeline as generation_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import FILES
from chara.wakeword.generation_pipeline import generate_dataset


class GenerationPortableTests(unittest.TestCase):
    def test_separate_generation_packages_without_training(self):
        from chara import Chara
        from chara.wakeword.generation.settings import GenerationSettings

        fixture = generation_fixture.PipelineTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        api = generation_fixture.FakeBrainBox()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generation"
            settings = GenerationSettings("computer", ["computer"], [])
            with (
                patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=api)),
                patch(
                    "brainbox.deciders.voice_analysis.wakeword_training.runtime.execution.run_training",
                    side_effect=AssertionError("generation must not train"),
                ),
            ):
                result = generate_dataset(settings, output)
                calls = api.tts_calls
                repeated = generate_dataset(settings, output)
            self.assertEqual(api.tts_calls, calls)
            self.assertEqual(result["archive_sha256"], repeated["archive_sha256"])
            self.assertTrue(list((output / "review").glob("*/record.json")))
            with zipfile.ZipFile(result["archive_path"]) as archive:
                self.assertEqual(set(archive.namelist()), FILES)
