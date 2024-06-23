from kaia.avatar.dub.languages.en import FloatDub, Template
from unittest import TestCase



class FloatTestCase(TestCase):
    def check(self, v, expected_s):
        template = Template('{value}', value=FloatDub(1000))
        s = template.to_str(dict(value=v))
        self.assertEqual(expected_s, s)
        actual_v = template.parse(s)['value']
        self.assertEqual(v, actual_v)

    def test_int(self):
        self.check(5,'five')

    def test_special(self):
        self.check(5.5, 'five and a half')

    def test_fraction(self):
        self.check(5.6, 'five point six')

    def test_fraction_2(self):
        self.check(5.67, 'five point sixty seven')

    def test_fraction_zero(self):
        self.check(5.03, 'five point zero three')

    def test_big_number(self):
        self.check(300, 'three hundred')