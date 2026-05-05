from grammatron import CardinalDub, PluralAgreement
from grammatron.dubs import DictTemplateDub, DubParameters
from unittest import TestCase

consumed_var = CardinalDub().as_variable('consumed')
plural_agreement = PluralAgreement(consumed_var, 'banana')
remaining_var = CardinalDub().as_variable('remaining')

dub = DictTemplateDub(f"I ate {plural_agreement} and {remaining_var} remained")


class DebugToStrTestCase(TestCase):
    def test_debug_to_str(self):
        params = DubParameters(debug_mode=True)
        result = dub.to_str(dict(consumed=3, remaining=2), params)
        self.assertEqual("I ate three bananas and two remained", result)
        self.assertEqual("three", consumed_var.debug_to_str_result)
        self.assertEqual("two", remaining_var.debug_to_str_result)
        self.assertEqual("three bananas", plural_agreement.debug_to_str_result)
