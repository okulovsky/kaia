import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    import numpy as np
except ImportError:
    np = None
from wakeword.generation.validation import FEATURES, check_completed, publish_manifest


@unittest.skipIf(np is None, "requires numpy")
class ArtifactTests(unittest.TestCase):
    def test_corrupt_artifact_rejected_after_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in FEATURES:
                np.save(root / (name + ".npy"), np.ones((2, 16, 96), dtype=np.float32))
            publish_manifest(root, {}, {}, [])
            check_completed(root)
            array = np.load(root / (FEATURES[0] + ".npy"))
            array[0, 0, 0] = float("nan")
            np.save(root / (FEATURES[0] + ".npy"), array)
            with self.assertRaises(ValueError):
                check_completed(root)

    def test_bad_shape_never_published(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in FEATURES:
                np.save(root / (name + ".npy"), np.ones((2, 15, 96), dtype=np.float32))
            with self.assertRaises(ValueError):
                publish_manifest(root, {}, {}, [])
            self.assertFalse((root / "manifest.json").exists())
