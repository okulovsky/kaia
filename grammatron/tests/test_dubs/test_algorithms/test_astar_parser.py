from grammatron import *
from unittest import TestCase
import datetime

C = VariableDub('test', CardinalDub(0,10))

class AstarParserTestCase(TestCase):
    def test_simple(self):
        t = DictTemplateDub(f"value {C}")
        parser = AStarParser(t)
        self.assertEqual('value six', parser.nearest_string('vlu sx'))

    def test_date(self):
        t = DictTemplateDub(f"value {VariableDub('date', DateDub())}")
        parser = AStarParser(t)
        value = datetime.date(2020,4,17)
        s = t.to_str(dict(date=value))
        self.assertEqual(s, parser.nearest_string(AStarParser.add_noise_to_string(s)))

    def test_list_dub(self):
        dub = ListDub(CardinalDub(10))
        parser = AStarParser(dub)
        self.assertEqual((1,5,3), parser.parse("on, fie an thee"))

    def test_failed_example(self):
        template = DictTemplateDub(f"{PluralAgreement(CardinalDub(10).as_variable('minutes'), 'minute')}, please")
        parser = AStarParser(template)
        print(parser.parse("Five minutes please"))
