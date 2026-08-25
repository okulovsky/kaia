import unittest

from grammatron import Template

from chara.paraphrasing.common import Paraphrase, ParsedTemplate


MONO = Template("yes")
MULTI = Template(en="the timer is set", ru="таймер заведен")


class ParaphrasePrepareTestCase(unittest.TestCase):
    """`prepare` must be idempotent.

    UtteranceParaphrasePipeline expands the cases up front, because the statistics need
    a parsed template, and ParaphrasePipeline expands whatever batch it is handed. If the
    second expansion re-parsed the original, a batch would arrive bigger than it was
    selected to be and each variant would be paraphrased and uploaded once per sibling.
    """

    def test_the_fixture_really_has_several_variants(self):
        self.assertEqual(1, len(ParsedTemplate.parse(MONO)))
        self.assertEqual(2, len(ParsedTemplate.parse(MULTI)))

    def test_a_fresh_case_is_expanded_per_variant(self):
        cases = Paraphrase([Paraphrase.Case(MONO, 'en'), Paraphrase.Case(MULTI, 'en')]).prepare()
        self.assertEqual(3, len(cases.cases))
        self.assertTrue(all(case.parsed_template is not None for case in cases.cases))

    def test_expanding_twice_changes_nothing(self):
        once = Paraphrase([Paraphrase.Case(MONO, 'en'), Paraphrase.Case(MULTI, 'en')]).prepare()
        twice = Paraphrase(once.successes).prepare()
        self.assertEqual(len(once.cases), len(twice.cases))
        self.assertEqual(
            [c.parsed_template.original_language for c in once.cases],
            [c.parsed_template.original_language for c in twice.cases],
        )

    def test_expanding_is_stable_however_many_times(self):
        cases = Paraphrase([Paraphrase.Case(MULTI, 'en')]).prepare()
        for _ in range(3):
            cases = Paraphrase(cases.successes).prepare()
        self.assertEqual(2, len(cases.cases))

    def test_a_single_selected_variant_stays_single(self):
        # This is the batch the selection hands over: one variant of a multi-variant
        # template. It must not fan back out into all of them.
        expanded = Paraphrase([Paraphrase.Case(MULTI, 'en')]).prepare()
        selected = [expanded.cases[0]]
        self.assertEqual(1, len(Paraphrase(selected).prepare().cases))


if __name__ == '__main__':
    unittest.main()
