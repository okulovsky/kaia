from avatar.utils import Sine, split_wav_by_amplitude
from unittest import TestCase

class WatAnalysisAndGenerationTestCase(TestCase):
    def test_analysis_and_generation(self):
        data = (Sine()
                .segment(0.3, 1)
                .segment(0.5, 2)
                .segment(0.01, 3)
                .segment(0.000001, 5)
                .bytes()
                )
        result = split_wav_by_amplitude(data)
        self.assertEqual(4, len(result))
        self.assertEqual(0.3, result[0].amplitude)
        self.assertEqual(0.5, result[1].amplitude)
        self.assertEqual(0.01, result[2].amplitude)
        self.assertEqual(0, result[3].amplitude)