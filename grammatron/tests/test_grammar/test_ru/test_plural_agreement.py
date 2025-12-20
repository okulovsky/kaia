from grammatron import *
from grammatron.grammars.ru import RuPluralAgreement, RuDeclension, RuGrammarRule
from unittest import TestCase
from enum import Enum

PARAMETERS = DubParameters(language='ru')

class Things(Enum):
    m = 'стол'
    f = 'кровать'
    n = 'окно'


class RuPluralAgreementTestCase(TestCase):
    def test_no_declension(self):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), "булочка")
        self.assertEqual('двадцать одна булочка', ag.to_str(dict(amount=21), PARAMETERS))
        self.assertEqual('двадцать две булочки', ag.to_str(dict(amount=22), PARAMETERS))
        self.assertEqual('двадцать пять булочек', ag.to_str(dict(amount=25), PARAMETERS))
        self.assertEqual('одиннадцать булочек', ag.to_str(dict(amount=11), PARAMETERS))
        self.assertEqual('двенадцать булочек', ag.to_str(dict(amount=12), PARAMETERS))
        self.assertEqual('пятнадцать булочек', ag.to_str(dict(amount=15), PARAMETERS))

    def test_with_declension(self):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), "булочка").grammar.ru(declension=RuDeclension.INSTRUMENTAL)
        self.assertEqual('двадцатью одной булочкой', ag.to_str(dict(amount=21), PARAMETERS))
        self.assertEqual('двадцатью двумя булочками', ag.to_str(dict(amount=22), PARAMETERS))
        self.assertEqual('двадцатью пятью булочками', ag.to_str(dict(amount=25), PARAMETERS))

    def test_with_enum(self):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), OptionsDub(Things).as_variable('item')).grammar.ru(declension=RuDeclension.INSTRUMENTAL)
        self.assertEqual('тремя столами', ag.to_str(dict(amount=3, item=Things.m), PARAMETERS))
        self.assertEqual('пятью кроватями', ag.to_str(dict(amount=5, item=Things.f), PARAMETERS))
        self.assertEqual('одним окном', ag.to_str(dict(amount=1, item=Things.n), PARAMETERS))

    def test_long_numerical(self):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), OptionsDub(Things).as_variable('item'))
        self.assertEqual('две тысячи триста сорок одна кровать', ag.to_str(dict(amount=2341, item=Things.f), PARAMETERS))

    def test_plural_agreement_with_variable(self):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), ToStrDub().as_variable('unit'))
        self.assertEqual('пять секунд', ag.to_str(dict(amount=5, unit='секунда'), PARAMETERS))



