from grammatron.tests.common import *

A = VariableDub('a', OptionsDub(['a','b','c']))
X = VariableDub('x', OptionsDub(['x', 'y', 'z']))
dub = IterationDub(DictTemplateDub(f"{A}", f", {X}"))


class IterationDubTestCase(TestCase):
    def test_tostr(self):
        self.assertEqual(', x, y, z', dub.to_str((dict(x='x'), dict(x='y'), dict(x='z'))))


    def test_integration(self):
        run_regex_integration_test(
            self,
            dub,
            [
                (),
                (dict(a='a'),),
                (dict(x='x'),),
                (dict(a='a'),dict(a='b'),dict(x='x'),),
            ],
            debug=True
        )
