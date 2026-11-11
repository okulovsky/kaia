import unittest

from chara.wakeword.training.metrics import calculate_metrics


class MetricTests(unittest.TestCase):
    def test_counts(self):
        result = calculate_metrics([0.5, 0.8, 0.1], [0.6, 0.2], [0.5, 0], 0.5, 40, 0.08)
        self.assertEqual(
            [result["supervised"][x] for x in ("TP", "FP", "TN", "FN")], [2, 1, 1, 1]
        )
        self.assertAlmostEqual(result["supervised"]["F1"], 2 / 3)
        self.assertEqual(result["background"]["positive_windows"], 1)
        self.assertAlmostEqual(
            result["background"]["threshold_windows_per_feature_hour"], 1125
        )

    def test_undefined_precision(self):
        result = calculate_metrics([0], [0], [0], 0.5, 16, 0.08)
        self.assertIsNone(result["supervised"]["precision"])
        self.assertEqual(result["supervised"]["F1"], 0)
        self.assertIsNone(result["background"]["waveform_hours"])
        with self.assertRaises(ValueError):
            calculate_metrics([0], [0], [0], 0.5, 0, 0.08)
