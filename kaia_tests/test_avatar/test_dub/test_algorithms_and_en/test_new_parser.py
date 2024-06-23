from unittest import TestCase
from kaia.avatar.dub.core.algorithms import RegexpParser
from kaia.avatar.dub.languages.en import *

class Parser(TestCase):
    def test_float_1(self):
        self.assertDictEqual(
            dict(f=22.3),
            RegexpParser(Template('{f}', f=FloatDub())).parse('twenty two point three')
        )

    def test_float_2(self):
        self.assertDictEqual(
            dict(f=20),
            RegexpParser(Template('{f} two point three', f=FloatDub())).parse('twenty two point three')
        )

    def test_longest_match(self):
        s = 'twenty two point three'
        match = RegexpParser(Template('{f}', f=FloatDub())).longest_substring_match(s)
        self.assertEqual(s, match.group(0))


