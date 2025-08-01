from grammatron.tests.common import *

class PluralAgreementTestCase(TestCase):
    def test_plural_agreement(self):
        t = DictTemplateDub(f"{PluralAgreement(CardinalDub(10).as_variable('seconds'), 'second')}")
        self.assertEqual("five seconds", t.to_str(dict(seconds=5)))
        self.assertEqual("one second", t.to_str(dict(seconds=1)))
