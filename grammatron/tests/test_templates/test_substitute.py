from grammatron.tests.common import *

class SubstituteTestCase(TestCase):
    def test_substitute(self):
        VAR = VariableDub("variable")
        template = Template(f"Variable is {VAR}")
        template = template.substitute(variable=VariableDub('variable', CardinalDub(10)))
        result = template.to_str(5)
        self.assertEqual("Variable is five", result)
