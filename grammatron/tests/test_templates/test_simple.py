from unittest import TestCase
from grammatron import Template, VariableDub

class SimplestTemplateTestCase(TestCase):
    def test_simplest_template(self):
        t = Template(f"A is {VariableDub('A')}")
        print(t.to_str(dict(A='A')))