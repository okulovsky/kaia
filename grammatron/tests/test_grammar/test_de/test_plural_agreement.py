import unittest
from grammatron import DubParameters, CardinalDub, OptionsDub
from grammatron.grammars.de import DePluralAgreement, DeGrammarRule, DeCasus, DeArticleType

PARAMETERS = DubParameters(language='de')


class TestDePluralAgreement(unittest.TestCase):

    def test_singular(self):
        ag = DePluralAgreement(CardinalDub().as_variable('amount'), 'Hund')
        result = ag.to_str(dict(amount=1), PARAMETERS)

        self.assertEqual("eins Hund", result)
        # Is it really literate? I think in this case it should be ein Hund, eine Gurke, etc.
        # Test for other Genus as well

    def test_plural(self):
        ag = DePluralAgreement(CardinalDub().as_variable('amount'), 'Hund')
        result = ag.to_str(dict(amount=3), PARAMETERS)
        self.assertIn('drei', result)
        self.assertIn('Hunde', result)

    def test_plural_five(self):
        ag = DePluralAgreement(CardinalDub().as_variable('amount'), 'Haus')
        result = ag.to_str(dict(amount=5), PARAMETERS)
        self.assertIn('fünf', result)
        self.assertIn('Häuser', result)

    def test_with_article_plural(self):
        # With definite article: article goes before the entire phrase → "die drei Gurken"
        ag = DePluralAgreement(
            CardinalDub().as_variable('amount'), 'Gurke'
        ).grammar.de(article_type=DeArticleType.WEAK)
        result = ag.to_str(dict(amount=3), PARAMETERS)
        self.assertEqual("die drei Gurken", result) # isn't it extremely specific case, like "(exactly these) three cucumbers"?


    def test_with_casus(self):
        ag = DePluralAgreement(
            CardinalDub().as_variable('amount'), 'Hund'
        ).grammar.de(casus=DeCasus.DATIV)
        result = ag.to_str(dict(amount=3), PARAMETERS)
        self.assertEqual('drei Hunden', result)


if __name__ == '__main__':
    unittest.main()
