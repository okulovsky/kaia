"""Legacy packaging preserves feature bytes and transfers only the allowlist."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from remote_training_fixtures import portable_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    sha256,
    write_json,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import FILES
from chara.wakeword.generation.packaging import package_dataset


class LegacyAdapterTests(unittest.TestCase):
    def test_repack_preserves_features_and_ignores_extra_files(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "generation"
            portable = portable_fixture(source)
            (portable / "unexpected.wav").write_bytes(b"must not transfer")
            before = sha256(source / "dataset/positive_features_train.npy")
            first = package_dataset(source)
            second = package_dataset(source / "dataset")
            self.assertEqual(first["corpus_id"], second["corpus_id"])
            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            self.assertEqual(before, sha256(portable / "positive_features_train.npy"))
            with zipfile.ZipFile(first["archive_path"]) as archive:
                self.assertEqual(set(archive.namelist()), FILES)
            manifest = read_json(portable / "manifest.json")
            self.assertNotIn("resource_folder", manifest["preparation"])

    def test_incomplete_legacy_dataset_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "generation"
            portable_fixture(source)
            path = source / "dataset/manifest.json"
            manifest = read_json(path)
            manifest["status"] = "failed"
            write_json(path, manifest)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                package_dataset(source)
