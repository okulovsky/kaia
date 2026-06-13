from chara.common.tools import Wav
from chara.common import Samples
from unittest import TestCase
from yo_fluq import FileIO

class WavEditableTestCase(TestCase):
    def test_read_write(self):
        w1 = Wav.one(Samples.lina/'lina1.wav').to_editable()
        w2 = Wav(w1.to_bytes()).to_editable()
        self.assertEqual(w1.info, w2.info)
        self.assertEqual(w1.data.shape, w2.data.shape)
        self.assertTrue(all(w1.data==w2.data))

        self.assertEqual(
            w2.to_bytes(),
            Wav.one(w2.to_bytes()).to_editable().to_bytes()
        )

    def test_slice(self):
        w = Wav.one(Samples.lina/'lina1.wav').to_editable()[1:2]
        self.assertEqual(1, w.duration_sec)
        self.assertEqual(1, Wav.one(w.to_bytes()).to_editable().duration_sec)



