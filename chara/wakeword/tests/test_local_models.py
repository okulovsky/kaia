import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
try:
    from wakeword.generation.local import texts
except ImportError:
    texts = None


class LocalEmbeddingTests(unittest.TestCase):
    def test_windows_safe_memmap_trimming(self):
        from wakeword.generation.local.embedding import trim_mmap

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "features.npy"
            values = np.zeros((4, 16, 96), dtype="float32")
            values[:2] = 1
            np.save(path, values)
            trim_mmap(path)
            self.assertEqual(np.load(path).shape, (2, 16, 96))
            np.save(path, np.zeros((1, 16, 96), dtype="float32"))
            with self.assertRaises(ValueError):
                trim_mmap(path)


@unittest.skipIf(texts is None, "requires host processing dependencies")
class LocalTextTests(unittest.TestCase):
    def test_checkpoint_tokenizer_namespace_is_compatible(self):
        import io

        from dp.preprocessing.text import SequenceTokenizer
        from wakeword.generation.local.phonemizer import TokenizerUnpickler

        loader = TokenizerUnpickler(io.BytesIO())
        self.assertIs(
            loader.find_class(
                "deep_phonemizer.preprocessing.text", "SequenceTokenizer"
            ),
            SequenceTokenizer,
        )

    def test_dictionary_word_generates_negatives_without_model_download(self):
        with patch("requests.get") as download:
            result = texts.generate_adversarial_texts("computer", 2)
            self.assertTrue(result)
            self.assertNotIn("computer", result)
            download.assert_not_called()

    def test_unknown_word_uses_explicit_checkpoint_only(self):
        from dp.phonemizer import Phonemizer

        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "model.pt"
            checkpoint.write_bytes(b"fixture")
            phones = lambda word: [] if word == "unknownfixture" else ["K AH0 M"]
            with (
                patch.object(texts.pronouncing, "phones_for_word", side_effect=phones),
                patch.object(texts.pronouncing, "search", return_value=["commuter"]),
                patch.object(
                    Phonemizer,
                    "from_checkpoint",
                    return_value=lambda word, lang: "[K][AH0][M]",
                ) as loader,
                patch("requests.get") as download,
            ):
                result = texts.generate_adversarial_texts(
                    "unknownfixture", 1, phonemizer_path=checkpoint
                )
                self.assertEqual(result, ["commuter"])
                loader.assert_called_once_with(str(checkpoint))
                download.assert_not_called()
                with self.assertRaises(ValueError):
                    texts.generate_adversarial_texts("unknownfixture", 1)


if __name__ == "__main__":
    unittest.main()
