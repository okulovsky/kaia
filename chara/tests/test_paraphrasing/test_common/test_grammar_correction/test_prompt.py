from chara.paraphrasing.common import GrammarCorrection
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import Template, CardinalDub, OptionsDub, PluralAgreement
from unittest import TestCase


class GrammarCorrectionPromptTestCase(TestCase):
    def _make_case(self, template):
        return GrammarCorrection([template]).prepare().cases[0]

    def _get_prompt(self, case):
        builder = PromptTaskBuilder('test')
        GrammarCorrection.Pipeline(builder)
        return builder._get_prompt(case)

    def test_russian_template_uses_russian_prompt(self):
        options = OptionsDub(['банан', 'яблоко']).as_variable('fruit')
        template = Template(ru=f"Я съел {PluralAgreement(CardinalDub().as_variable('amount'), options)}")
        prompt = self._get_prompt(self._make_case(template))
        self.assertIn('учитель русского языка', prompt)

    def test_german_template_uses_german_prompt(self):
        template = Template(de=f"Ich gehe in {OptionsDub(['bathroom', 'living room']).as_variable('room')}")
        prompt = self._get_prompt(self._make_case(template))
        self.assertIn('Deutschlehrer', prompt)
