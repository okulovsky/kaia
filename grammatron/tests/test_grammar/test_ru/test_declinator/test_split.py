from grammatron.grammars.ru import Declinator
from grammatron.grammars.common import WordProcessor
import unittest

class TestSplitTextFragments(unittest.TestCase):
    def test_basic_sentence(self):
        text = "Привет, мир!"
        expected = [
            WordProcessor.Fragment('Привет', True),
            WordProcessor.Fragment(', ', False),
            WordProcessor.Fragment('мир', True),
            WordProcessor.Fragment('!', False)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_internal_dash(self):
        text = "премьер-министр выступил"
        expected = [
            WordProcessor.Fragment('премьер-министр', True),
            WordProcessor.Fragment(' ', False),
            WordProcessor.Fragment('выступил', True)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_surrounded_dash(self):
        text = "ветер - сильный"
        expected = [
            WordProcessor.Fragment('ветер', True),
            WordProcessor.Fragment(' - ', False),
            WordProcessor.Fragment('сильный', True)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_multiple_punctuation(self):
        text = "Он сказал: «Привет!»"
        expected = [
            WordProcessor.Fragment('Он', True),
            WordProcessor.Fragment(' ', False),
            WordProcessor.Fragment('сказал', True),
            WordProcessor.Fragment (': «', False),
            WordProcessor.Fragment('Привет', True),
            WordProcessor.Fragment('!»', False)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_mixed_case(self):
        text = "Юго-Западный ветер"
        expected = [
            WordProcessor.Fragment('Юго-Западный', True),
            WordProcessor.Fragment(' ', False),
            WordProcessor.Fragment('ветер', True)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_leading_and_trailing_punctuation(self):
        text = '"Сильный ветер," — подумал он.'
        expected = [
            WordProcessor.Fragment('"', False),
            WordProcessor.Fragment('Сильный', True),
            WordProcessor.Fragment(' ', False),
            WordProcessor.Fragment('ветер', True),
            WordProcessor.Fragment('," — ', False),
            WordProcessor.Fragment('подумал', True),
            WordProcessor.Fragment(' ', False),
            WordProcessor.Fragment('он', True),
            WordProcessor.Fragment('.', False)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_whitespace_only(self):
        text = "   \t\n"
        expected = [
            WordProcessor.Fragment('   \t\n', False)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_empty_string(self):
        text = ""
        expected = []
        self.assertEqual(WordProcessor.word_split(text), expected)

    def test_single_word(self):
        text = "Слово"
        expected = [
            WordProcessor.Fragment('Слово', True)
        ]
        self.assertEqual(WordProcessor.word_split(text), expected)
