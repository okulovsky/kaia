from eaglesong.templates import *
from unittest import TestCase
from pprint import pprint

class HumanReadableReprTestCase(TestCase):
    def test_human_readable(self):
        hours = TemplateVariable("hours",CardinalDub(10),"some description")
        template = Template(
            f'{hours} {PluralAgreement("hours").as_variable()}',
            f'{hours} {PluralAgreement("hours").as_variable()}, {CardinalDub(10).as_variable("minutes")} {PluralAgreement("minutes").as_variable()}',
        )
        self.assertEqual('some description', template.attached_variables['hours'].description)
        self.assertEqual(
            ['{hours} [hour|hours]', '{hours} [hour|hours], {minutes} [minute|minutes]'],
            template.string_templates
        )
