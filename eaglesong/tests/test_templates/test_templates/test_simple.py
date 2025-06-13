from unittest import TestCase
from eaglesong.templates import Template, TemplateVariable

class SimplestTemplateTestCase(TestCase):
    def test_simplest_template(self):
        t = Template(f"A is {TemplateVariable('A')}")
        print(t.to_str(dict(A='A')))