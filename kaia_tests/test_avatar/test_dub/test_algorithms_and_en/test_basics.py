from unittest import TestCase
from kaia.avatar.dub.languages.en import *


class BasicsTestCase(TestCase):
    def test_to_str(self):
        template = Template('Test {value}', value = CardinalDub(0, 100))
        s = template.to_str(dict(value=50))
        self.assertEqual('Test fifty', s)

    def test_parse(self):
        template = Template('Test {value}', value=CardinalDub(0, 100))
        value = template.parse('Test fifty')
        self.assertDictEqual(dict(value=50), value)



