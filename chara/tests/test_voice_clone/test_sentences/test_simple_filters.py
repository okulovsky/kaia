from chara.voice_clone.sentences.corpus_filter.simple_filters import *
import unittest
from unittest.mock import Mock

class TestTypographicReplacement(unittest.TestCase):
    def test_typographic_replacement(self):
        filt = TypographicReplacement(replacements={"'": "‘’‚‛"})
        self.assertEqual(filt.filter("This is ‘quoted’ text"), "This is 'quoted' text")
        self.assertEqual(filt.filter("No replacements here"), "No replacements here")

class TestBadSymbolsFilter(unittest.TestCase):
    def test_only_allowed_symbols(self):
        filt = BadSymbolsFilter(allowed_symbols=set("abc "))
        self.assertEqual(filt.filter("a b c"), "a b c")
        self.assertIsNone(filt.filter("a b d"))

class TestLengthFilter(unittest.TestCase):
    def test_within_bounds(self):
        filt = LengthFilter(min_length=5, max_length=10)
        self.assertEqual(filt.filter("123456"), "123456")
        self.assertIsNone(filt.filter("1234"))
        self.assertIsNone(filt.filter("12345678901"))

class TestTooMuchCapitalLettersFilter(unittest.TestCase):
    def test_capital_letters(self):
        filt = TooMuchCapitalLettersFilter(max_capital_letters=3)
        self.assertEqual(filt.filter("This Is ok"), "This Is ok")
        self.assertIsNone(filt.filter("TOO MANY CAPS HERE"))
        self.assertEqual(filt.filter("some lower and Two Caps"), "some lower and Two Caps")

class TestNoAbbreviationsFilter(unittest.TestCase):
    def test_abbreviation_detection(self):
        filt = NoAbbreviationsFilter.from_language(Language.English())
        self.assertEqual(filt.filter("This Is Fine"), "This Is Fine")
        self.assertIsNone(filt.filter("ThiSIsWrong"))
        self.assertIsNone(filt.filter("ThIs also wrong"))