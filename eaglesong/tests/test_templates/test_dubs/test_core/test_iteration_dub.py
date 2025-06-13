from eaglesong.tests.test_templates.test_dubs.common import *

A = TemplateVariable('a', OptionsDub(['a','b','c']))
X = TemplateVariable('x', OptionsDub(['x', 'y', 'z']))
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
