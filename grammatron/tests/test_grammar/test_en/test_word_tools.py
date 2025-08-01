import unittest
from grammatron.grammars.en import *

class TestEnglishWordTools(unittest.TestCase):
    def test_is_noun(self):
        test_cases = [
            ("run", 'run'),
            ("book", 'book'),
            ("books", 'book'),
            ("corpora", 'corpus'),
            ("quickly", None),
            ("beautiful", None)
        ]
        for word, expected in test_cases:
            with self.subTest(word=word):
                self.assertEqual(expected, EnglishWordTools.get_noun_vocabulary_form(word))

    def test_to_plural(self):
        test_cases = [
            ("book", "books"),
            ("corpus", "corpuses"),
            ("glass", "glasses"),
            ("child", "children"),
            ("mouse", "mice"),
            ("bus", "buses"),
            ("analysis", "analyses"),
            ("datum", "data"),
            ("tooth", "teeth"),
        ]
        for word, expected in test_cases:
            with self.subTest(word=word):
                self.assertEqual(expected, EnglishWordTools.word_to_plural(word))

if __name__ == '__main__':
    unittest.main()
