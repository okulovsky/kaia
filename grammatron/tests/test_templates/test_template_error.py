from unittest import TestCase
from grammatron import Template, OptionsDub

class TemplateErrorsTestCase(TestCase):
    def test_dub_without_variable(self):
        dub = OptionsDub(['a','b'])
        print(f"Variable {dub}")
        with self.assertRaises(ValueError):
            Template(f"Variable {dub}")
