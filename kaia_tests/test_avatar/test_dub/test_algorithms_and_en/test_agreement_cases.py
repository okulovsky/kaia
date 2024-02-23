from kaia.avatar.dub.languages.en import *
from unittest import TestCase

class SpecialTestCases(TestCase):
    def test_agreement(self):
        template = Template(
            '{amount} {amount_word}',
            amount = CardinalDub(0, 10),
            amount_word = PluralAgreement('amount', 'minute','minutes')
        )
        self.assertEqual('one minute', template.to_str(dict(amount=1)))
        self.assertEqual('two minutes', template.to_str(dict(amount=2)))
        self.assertDictEqual(dict(amount=1), template.parse('one minute'))
        self.assertDictEqual(dict(amount=2), template.parse('two minutes'))