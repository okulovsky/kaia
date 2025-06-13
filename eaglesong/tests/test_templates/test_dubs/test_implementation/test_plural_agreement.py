from eaglesong.tests.test_templates.test_dubs.common import *

class PluralAgreementTestCase(TestCase):
    def test_plural_agreement(self):
        t = DictTemplateDub(f"{CardinalDub(10).as_variable('seconds')} {PluralAgreement('seconds').as_variable()}")
        self.assertEqual("five seconds", t.to_str(dict(seconds=5)))
        self.assertEqual("one second", t.to_str(dict(seconds=1)))
