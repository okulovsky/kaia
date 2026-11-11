import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wakeword.generation.local.normalization import normalize
from wakeword.generation.local.resources import ResourceInstaller
from wakeword.generation.settings import GenerationSettings


class HostProcessingTests(unittest.TestCase):
    def test_normalize_stereo_resample_and_reject_nan(self):
        with tempfile.TemporaryDirectory(prefix="wakeword with spaces ") as tmp:
            root = Path(tmp)
            sf.write(
                root / "source.wav", np.ones((800, 2), dtype="float32") * 0.1, 8000
            )
            normalize(root / "source.wav", root / "out.wav")
            info = sf.info(root / "out.wav")
            self.assertEqual(
                (info.samplerate, info.channels, info.frames), (16000, 1, 1600)
            )
            sf.write(
                root / "bad.wav",
                np.array([np.nan], dtype="float32"),
                16000,
                subtype="FLOAT",
            )
            with self.assertRaises(ValueError):
                normalize(root / "bad.wav", root / "out.wav")

    def test_local_resources_reuse_hashes_acav_and_corruption(self):
        with tempfile.TemporaryDirectory(prefix="wakeword cache ") as tmp:
            root = Path(tmp)
            sf.write(root / "audio.wav", np.ones(1000, dtype="float32") * 0.1, 16000)
            data = np.arange(100 * 16 * 96, dtype="float32").reshape(100, 16, 96)
            np.save(root / "acav.npy", data)
            specs = [
                {
                    "id": kind + ".wav",
                    "kind": kind,
                    "source": (root / "audio.wav").as_uri(),
                    "revision": "test",
                }
                for kind in ("background_wav", "rir_wav")
            ]
            specs.append(
                {
                    "id": "acav.npy",
                    "kind": "acav",
                    "source": (root / "acav.npy").as_uri(),
                    "revision": "test",
                }
            )
            installer = ResourceInstaller(root / "cache")
            with patch("importlib.metadata.version", return_value="fixture"):
                manifest = installer.prepare(specs)
                self.assertEqual(manifest, installer.load(specs))
                artifact = manifest["resources"][-1]["artifacts"][0]
                actual = np.load(installer.root / artifact["file"])
                np.testing.assert_array_equal(actual, data[:10])
                self.assertEqual(installer.prepare(specs), manifest)
                path = installer.root / artifact["file"]
                path.write_bytes(b"corrupt")
                with self.assertRaises(ValueError):
                    installer.load(specs)

    def test_old_schema_and_piper_backends_are_rejected(self):
        with self.assertRaises(ValueError):
            GenerationSettings(
                "computer", ["computer"], [], schema_version=1
            ).validate()
        with self.assertRaises(ValueError):
            GenerationSettings(
                "computer", ["computer"], [], synthesis_backend="piper"
            ).validate()

    def test_config_resource_folder_is_relative_to_json(self):
        import json

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "name": "computer",
                        "target_variants": ["computer"],
                        "resource_specs": [],
                        "resource_folder": "cache",
                    }
                )
            )
            self.assertEqual(
                GenerationSettings.read(path).resource_folder, str(root / "cache")
            )

    def test_space_check_prevents_large_download_on_small_disk(self):
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as tmp:
            installer = ResourceInstaller(tmp)
            with patch("shutil.disk_usage", return_value=SimpleNamespace(free=1024)):  # noqa: SIM117 - Keep acquisition separate from the expected failure scope.
                with self.assertRaises(RuntimeError):
                    installer.check_space(
                        [
                            {
                                "id": "acav.npy",
                                "kind": "acav",
                                "source": "https://example/acav.npy",
                                "revision": "1",
                            }
                        ]
                    )

    def test_no_worker_imports_or_tasks(self):
        root = Path(__file__).resolve().parents[1] / "generation"
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8-sig")
            self.assertNotIn("from brainbox.deciders import WakewordData", text)
            self.assertNotIn("WakewordData.new_task", text)


if __name__ == "__main__":
    unittest.main()
