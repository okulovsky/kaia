from kaia.persona.dub.languages.en import *
from unittest import TestCase
from enum import Enum

class TestEnum(Enum):
    First = 1
    Second = 2


class ParseTestCase(TestCase):
    def test_cardinals(self):
        TestingTools(CardinalDub(-100, 100)).test_all_unit(self)

    def test_ordinals(self):
        TestingTools(OrdinalDub(0, 100)).test_all_unit(self)

    def test_enum(self):
        TestingTools(EnumDub(TestEnum)).test_all_unit(self)

    def test_template(self):
        template = Template(
            'word {number} and {number_1}',
            number = CardinalDub(0, 10),
            number_1 = CardinalDub(0, 10)
        )
        self.assertDictEqual(
            dict(number = 1, number_1 = 2),
            template.parse('word one and two')
        )
        TestingTools(template).test_all_unit(self)

    def test_template_with_two_lines(self):
        template = Template(
            'cardinal {cardinal}',
            'ordinal {ordinal}',
            cardinal = CardinalDub(0,10),
            ordinal = OrdinalDub(0,10)
        )
        TestingTools(template).test_all_unit(self)

    def test_agreement(self):
        template = Template(
            '{amount} {amount_word}',
            amount = CardinalDub(0, 10),
            amount_word = PluralAgreement('amount', 'minute','minutes')
        )
        self.assertEqual('one minute', template.to_str(dict(amount=1)))
        self.assertEqual('two minutes', template.to_str(dict(amount=2)))
        TestingTools(template).test_all_unit(self)

    def test_date_dub(self):
        TestingTools(DateDub()).test_all_unit(self)

    def test_timedelta_dub(self):
        TestingTools(TimedeltaDub()).test_all_unit(self)
