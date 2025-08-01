import unittest
from typing import List
from phonix.daemon.processing.sound_buffer import SoundBuffer
from phonix.daemon.inputs import MicData

class TestSoundBuffer(unittest.TestCase):
    def test_initial_state(self):
        buf = SoundBuffer(max_time_seconds=1.0)
        # Initially, no sample rate, empty buffer, not full
        self.assertIsNone(buf.sample_rate)
        self.assertEqual(buf.buffer, [])
        self.assertFalse(buf.is_full)

    def test_add_small_samples_not_full(self):
        # max_time_seconds=1.0 at 8000 Hz => max_samples = 8000
        buf = SoundBuffer(max_time_seconds=1.0)
        small = [0] * 1000
        buf.add(MicData(8000, small))
        # buffer under capacity, is_full stays False
        self.assertEqual(buf.buffer, small)
        self.assertFalse(buf.is_full)

    def test_exact_boundary_not_full(self):
        # max_time_seconds=0.5 at 4000 Hz => max_samples = 2000
        buf = SoundBuffer(max_time_seconds=0.5)
        sr = 4000
        exact = list(range(2000))
        buf.add(MicData(sr, exact))
        # exactly at capacity, no trimming, is_full False
        self.assertEqual(len(buf.buffer), 2000)
        self.assertEqual(buf.buffer, exact)
        self.assertFalse(buf.is_full)

    def test_overflow_sets_full(self):
        # max_time_seconds=0.5 at 4000 Hz => max_samples = 2000
        buf = SoundBuffer(max_time_seconds=0.5)
        sr = 4000
        samples = list(range(2500))
        buf.add(MicData(sr, samples))
        # buffer should be trimmed to last 2000 samples and marked full
        self.assertEqual(len(buf.buffer), 2000)
        self.assertEqual(buf.buffer, samples[-2000:])
        self.assertTrue(buf.is_full)

    def test_subsequent_add_after_full(self):
        # Once full, further adds still trigger trimming and remain full
        buf = SoundBuffer(max_time_seconds=0.1)
        sr = 1000
        # capacity = 100 samples
        buf.add(MicData(sr, list(range(150))))  # overflow => full
        self.assertTrue(buf.is_full)
        first_snapshot = buf.buffer.copy()

        # add 10 more => length 110>100, trimmed back to 100
        buf.add(MicData(sr, list(range(10))))
        self.assertTrue(buf.is_full)
        self.assertEqual(len(buf.buffer), 100)
        # buffer should equal last 100 of (first_snapshot + new 10)
        expected = (first_snapshot + list(range(10)))[-100:]
        self.assertEqual(buf.buffer, expected)

    def test_change_sample_rate_resets_full(self):
        buf = SoundBuffer(max_time_seconds=1.0)
        # fill buffer to overflow
        buf.add(MicData(8000, [1] * 9000))  # capacity 8000 => full
        self.assertTrue(buf.is_full)
        # change sample rate clears buffer and resets is_full
        buf.add(MicData(16000, [2] * 10))
        self.assertEqual(buf.sample_rate, 16000)
        self.assertEqual(buf.buffer, [2] * 10)
        self.assertFalse(buf.is_full)

if __name__ == '__main__':
    unittest.main()
