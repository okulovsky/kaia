from grammatron.tests.common import *

class OrdinalDubTestCase(TestCase):
    def test_simple(self):
        dub = OrdinalDub(0,100)
        self.assertEqual('fourth', dub.to_str(4))
        self.assertEqual('zeroth', dub.to_str(0))
        self.assertEqual('tenth', dub.to_str(10))
        self.assertEqual('forty-fifth', dub.to_str(45))

        self.assertEqual('1st', dub.to_str(1, DubParameters(False)))
        self.assertEqual('21st', dub.to_str(21, DubParameters(False)))
        self.assertEqual('32nd', dub.to_str(32, DubParameters(False)))
        self.assertEqual('43rd', dub.to_str(43, DubParameters(False)))
        self.assertEqual('55th', dub.to_str(55, DubParameters(False)))

    def test_parser_full(self):
        dub=OrdinalDub(0,100)
        for spoken in [True, False]:
            parser = RegexParser(dub, DubParameters(spoken=spoken))
            self.assertEqual(21, parser.parse("21st"))
            self.assertEqual(21, parser.parse("twenty-first"))

    def test_regex(self):
        run_regex_integration_test(
            self,
            OrdinalDub(0,100),
            range(0,100),
        )