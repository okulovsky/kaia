import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wakeword.generation.dto import AudioCase
from wakeword.generation.io import read_json
from wakeword.generation.review import save_review
from wakeword.generation.run_state import check_settings, run_lock
from wakeword.generation.settings import GenerationSettings


class StateTests(unittest.TestCase):
    def test_settings_before_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = GenerationSettings("computer", ["computer"], [])
            with run_lock(folder):
                check_settings(folder, settings)
                check_settings(folder, settings)
                settings.min_vosk_confidence = 0.9
                with self.assertRaises(ValueError):
                    check_settings(folder, settings)

    def test_review_keeps_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.wav"
            source.write_bytes(b"original")
            case = AudioCase(
                "sample",
                "sample",
                "positive",
                "train",
                42,
                0,
                "computer",
                source_audio=source,
                recognition=[],
                error_stage="recognition",
                reason_code="word_not_found",
            )
            path = save_review(root, case)
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual((path / "audio.wav").read_bytes(), b"original")
            self.assertEqual(
                read_json(path / "record.json")["reason_code"], "word_not_found"
            )
