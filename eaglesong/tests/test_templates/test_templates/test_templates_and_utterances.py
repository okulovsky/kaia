from unittest import TestCase
from eaglesong.templates import *
from dataclasses import dataclass



class TemplateToStrParseTestCase(TestCase):
    def test_untyped(self):
        t = Template(f"x={CardinalDub(10).as_variable('x')}")
        value = t.parse('x=5')
        self.assertEqual(dict(x=5), value)
        self.assertRaises(Exception, lambda: t.utter(y=5))
        u = t.utter(5)
        self.assertEqual(dict(x=5), u.value)
        u = t.utter(x=5)
        self.assertEqual(dict(x=5), u.value)
        u = t.utter(dict(x=5))
        self.assertEqual(dict(x=5), u.value)



    def test_typed(self):
        @dataclass
        class MyClass:
            x: int
        t = Template(f"x={CardinalDub(10).as_variable('x')}").with_type(MyClass)
        value = t.parse('x=5')
        self.assertIsInstance(value, MyClass)
        self.assertEqual(5, value.x)

        self.assertRaises(Exception, lambda:t.utter(x=5))
        u = t.utter(MyClass(5))
        self.assertEqual(5, u.value.x)


