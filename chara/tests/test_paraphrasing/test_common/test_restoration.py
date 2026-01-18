from unittest import TestCase
from chara.paraphrasing.common import ParsedTemplate, ParaphraseCase
from grammatron import Template, PluralAgreement, CardinalDub

class RestorationTestCase(TestCase):
    def test_restoration(self):
        template = Template(f"The answer is {PluralAgreement(CardinalDub(10).as_variable('variable'),'variable')}")
        parsed_template = ParsedTemplate.parse(template)[0]
        s = "It's {variable/variable}! That's the answer"
        new_template = parsed_template.restore_template(s)
        self.assertEqual("It's one variable! That's the answer", new_template.to_str(dict(variable=1)))
        self.assertEqual("It's two variables! That's the answer", new_template.to_str(dict(variable=2)))

