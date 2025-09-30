from dataclasses import dataclass
from grammatron import *
from unittest import TestCase

@dataclass
class MyClass:
    A: int
    B: int|None

class NoneInTemplateTestCase(TestCase):
    def test_none(self):
        t = Template(f"A={VariableDub('A')}, B={VariableDub('B')}", f"A={VariableDub('A')}, B is absent").with_type(MyClass)
        self.assertEqual('A=5, B=6', t.to_str(MyClass(5,6)))
        self.assertEqual('A=5, B is absent', t.to_str(MyClass(5, None)))


