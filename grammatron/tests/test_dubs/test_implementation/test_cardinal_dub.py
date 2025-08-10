from grammatron.tests.common import *

class CardinalDubTestCase(TestCase):
    def test_simple(self):
        dub = CardinalDub(0, 100)
        self.assertEqual('four', dub.to_str(4))
        self.assertEqual('zero', dub.to_str(0))
        self.assertEqual('ten', dub.to_str(10))
        self.assertEqual('forty-five', dub.to_str(45))

        self.assertEqual('21', dub.to_str(21, DubParameters(False)))

    def test_parser_full(self):
        dub=CardinalDub(0,100)
        for spoken in [True, False]:
            parser = RegexParser(dub, DubParameters(spoken=spoken))
            self.assertEqual(21, parser.parse("21"))
            self.assertEqual(21, parser.parse("twenty-one"))

    def test_regex(self):
        run_regex_integration_test(
            self,
            CardinalDub(0,100),
            range(0,100),
        )