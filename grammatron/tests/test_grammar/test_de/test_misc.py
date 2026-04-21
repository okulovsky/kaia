import unittest
from grammatron import DubParameters, CardinalDub
from grammatron.grammars.de import DeDeclinator, DeCasus, DeNumerus, DeArticleType, DePluralAgreement, DeGrammarRule

PARAMETERS = DubParameters(language='de')


class TestDeDeclinator(unittest.TestCase):

    def test_unknown_noun_unchanged(self):
        result = DeDeclinator.declinate('Xyzblorp', casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR)
        self.assertEqual('Xyzblorp', result)

    def test_word_selection_stops_after_first_noun(self):
        result = DeDeclinator.declinate(
            'kleine Gurke mit dem Sosse',
            casus=DeCasus.DATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('der kleinen Gurke mit dem Sosse', result)

    def test_punctuation_preserved(self):
        result = DeDeclinator.declinate(
            'frischer Kaffee, heiß',
            casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.STRONG,
        )
        self.assertIn(',', result)

    def test_no_grammar_unchanged(self):
        result = DeDeclinator.declinate('Hund')
        self.assertEqual('Hund', result)

    def test_empty_text(self):
        result = DeDeclinator.declinate('')
        self.assertEqual('', result)
