import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wakeword.generation.processing import extract_archive
from wakeword.generation.settings import GenerationSettings


class FoundationTests(unittest.TestCase):
    def test_confidence(self):
        settings = GenerationSettings("computer", ["computer"], [])
        self.assertEqual(settings.canonical()["min_vosk_confidence"], 0.7)
        for value in (float("nan"), float("inf"), -0.1, 1.1, True, "0.7"):
            settings.min_vosk_confidence = value
            with self.assertRaises(ValueError):
                settings.validate()

    def test_count_validation(self):
        settings = GenerationSettings("computer", ["computer"], [])
        settings.counts["positive_train"] = True
        with self.assertRaises(ValueError):
            settings.validate()

    def test_archive_traversal(self):
        for name in ("../escape", "/absolute", "C:/absolute", "..\\escape"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "input.zip"
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr(name, "payload")
                with self.assertRaises(ValueError):
                    extract_archive(source, root / "output")
                self.assertFalse((root / "escape").exists())

    def test_archive_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / "input.zip", "w") as archive:
                archive.writestr("samples/one.wav", b"payload")
            extract_archive(root / "input.zip", root / "output")
            self.assertEqual((root / "output/samples/one.wav").read_bytes(), b"payload")


if __name__ == "__main__":
    unittest.main()
