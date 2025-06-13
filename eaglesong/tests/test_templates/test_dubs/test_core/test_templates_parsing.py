from eaglesong.templates.dubs import *
from unittest import TestCase
from dataclasses import dataclass


C = TemplateVariable("c", CardinalDub(0,10))
O = TemplateVariable("o", OrdinalDub(0,10))

class DateDubParseTestCase(TestCase):
    def test_one_variable(self):
        parser = RegexParser(DictTemplateDub(f"value {C}"))
        result = parser.parse('value five')
        self.assertEqual(dict(c=5), result)

    def test_two_variable(self):
        parser = RegexParser(DictTemplateDub(f"{O} value {C}"))
        result = parser.parse("third value seven")
        self.assertEqual(dict(o=3, c=7), result)

    def test_alternative(self):
        parser = RegexParser(DictTemplateDub(f'{O}',f'{C}'))
        self.assertEqual(dict(o=3), parser.parse('third'))
        self.assertEqual(dict(c=6), parser.parse('six'))

    def test_nested(self):
        T = TemplateVariable("nested", DictTemplateDub(f"x {C}"))
        parser = RegexParser(DictTemplateDub(f'{O} {T}'))
        self.assertEqual({'o': 3, 'nested': {'c': 7}}, parser.parse("third x seven"))

    def test_dataclass(self):
        @dataclass
        class MyClass:
            a: int
            b: int

        template = DataclassTemplateDub(
            MyClass,
            f"a={CardinalDub(10).as_variable('a')}, b={CardinalDub(10).as_variable('b')}"
        )

        s = template.to_str(MyClass(2,3))
        self.assertEqual('a=two, b=three',s)

        v = RegexParser(template).parse("a=seven, b=two")
        self.assertIsInstance(v, MyClass)
        self.assertEqual(7, v.a)
        self.assertEqual(2, v.b)

