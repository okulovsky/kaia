import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wakeword.generation.positives.verification import RejectedAudio, verify
from wakeword.generation.progress import AttemptLedger


class VerificationTests(unittest.TestCase):
    def recognition(self, conf):
        return [
            {"word": "hi", "start": 0.1, "end": 0.3, "conf": 1},
            {"word": "computer", "start": 0.5, "end": 0.9, "conf": conf},
            {"word": "go", "start": 1.1, "end": 1.3, "conf": 1},
        ]

    def test_threshold_and_crop(self):
        for confidence in (0.7, 0.71):
            crop = verify("computer", self.recognition(confidence), 1.5, "Hi ", " go.")
            self.assertAlmostEqual(crop.start, 0.4)
            self.assertAlmostEqual(crop.end, 1.0)
        with self.assertRaises(RejectedAudio) as error:
            verify("computer", self.recognition(0.69), 1.5, "Hi ", " go.")
        self.assertEqual(error.exception.reason, "low_confidence")

    def test_empty_missing_and_wrong_word(self):
        for recognition in (
            [],
            self.recognition(None),
            [{"word": "other", "start": 0, "end": 1, "conf": 1}],
        ):
            with self.assertRaises(RejectedAudio):
                verify("computer", recognition, 1.5, "Hi ", " go.")

    def test_invalid_timestamps(self):
        recognition = self.recognition(1)
        recognition[1]["end"] = 10
        with self.assertRaises(RejectedAudio):
            verify("computer", recognition, 1.5, "Hi ", " go.")

    def test_permitted_variant_uses_original_closest_slice_rule(self):
        recognition = self.recognition(0.9)
        recognition[1]["word"] = "computers"
        crop = verify(
            "computer",
            recognition,
            1.5,
            "Hi ",
            " go.",
            allowed_variants=["computer", "computers"],
        )
        self.assertEqual(crop.recognition[0]["word"], "computers")

    def test_budget_survives_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = AttemptLedger(folder, 2)
            first = ledger.reserve(42)
            resumed = AttemptLedger(folder, 2)
            self.assertEqual(resumed.data["attempts"][0], first)
            for seed in range(5):
                resumed.reserve(seed)
            with self.assertRaises(RuntimeError):
                AttemptLedger(folder, 2).reserve(100)
