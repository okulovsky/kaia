from grammatron import CardinalDub, DubParameters, RegexParser
from grammatron.grammars.ru import *
from unittest import TestCase

class RuCardinalDubTestCase(TestCase):
    def test_no_rule(self):
        s = CardinalDub().to_str(10, DubParameters(language='ru'))
        self.assertEqual("десять", s)

    def test_given_rule(self):
        s = CardinalDub().to_str(10, DubParameters(language='ru', grammar_rule=RuGrammarRule(RuDeclension.GENITIVE)))
        self.assertEqual("десяти", s)

    def test_default_rule(self):
        s = CardinalDub().grammar.ru(RuDeclension.GENITIVE).to_str(10, DubParameters(language='ru'))
        self.assertEqual("десяти", s)

    def test_parse(self):
        parser = RegexParser(CardinalDub(20), DubParameters(language='ru'))
        self.assertEqual(10, parser.parse("десять"))
        self.assertEqual(10, parser.parse("десятью"))