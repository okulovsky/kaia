from dataclasses import dataclass
from pathlib import Path
from unittest import TestCase

from foundation_kaia.misc import Loc
from chara import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, IImageScenario
from chara.images.common.drawing import DrawingCase, VariantCase, DrawingPipeline


@dataclass
class _StubScenario(IImageScenario):
    character: Character
    theme: Theme
    activity: str
    tag: str = ''

    def to_workflow(self):
        raise NotImplementedError

    def to_prompt(self) -> str:
        return f'prompt-{self.tag}'


def _character(name: str) -> Character:
    return Character(name=name, gender=Character.Gender.Feminine, description='desc')


def _case(tag: str) -> DrawingCase:
    scenario = _StubScenario(_character('Miku'), Theme(location='forest'), 'cooking', tag)
    return DrawingCase(scenario=scenario, image=Path(f'/tmp/{tag}.png'))


def _set_variant(name: str):
    def pipeline(cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        for case in cases.cases:
            if case.variants is None:
                case.variants = {}
            case.variants[name] = VariantCase(prompt=f'{name}-{case.scenario.tag}')
        return cases
    return pipeline


def _fail_for_tag(tag_to_fail: str):
    def pipeline(cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        for case in cases.cases:
            if case.scenario.tag == tag_to_fail:
                case.error = 'boom'
        return cases
    return pipeline


def _apply_variant_pipelines(cases: CaseCollection[DrawingCase], variant_pipelines: dict) -> CaseCollection[DrawingCase]:
    pipeline = DrawingPipeline(variant_pipelines=variant_pipelines)
    return Chara.call(pipeline._run_variant_pipelines)(cases)


class ApplyVariantPipelinesTestCase(TestCase):
    def test_variant_pipelines_run_in_sequence_and_accumulate(self):
        case = _case('main')

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = _apply_variant_pipelines(
                CaseCollection([case]), {'a': _set_variant('a'), 'b': _set_variant('b')}
            )

        merged = result.cases[0]
        self.assertEqual({'a', 'b'}, set(merged.variants.keys()))
        self.assertEqual('a-main', merged.variants['a'].prompt)
        self.assertEqual('b-main', merged.variants['b'].prompt)

    def test_error_from_one_pipeline_is_nullified_before_the_next(self):
        failing = _case('a')
        ok = _case('b')

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = _apply_variant_pipelines(
                CaseCollection([failing, ok]),
                {'first': _fail_for_tag('a'), 'second': _set_variant('second')},
            )

        by_tag = {c.scenario.tag: c for c in result.cases}
        # 'a' failed the 'first' variant pipeline, so it never got that variant -
        # but the error must not stop it from going through 'second'.
        self.assertIsNone(by_tag['a'].error)
        self.assertNotIn('first', by_tag['a'].variants or {})
        self.assertIn('second', by_tag['a'].variants)
        self.assertIn('second', by_tag['b'].variants)

    def test_cases_that_failed_review_are_untouched_and_returned(self):
        already_erroneous = _case('rejected')
        already_erroneous.error = 'multiple people'
        ok = _case('ok')

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = _apply_variant_pipelines(
                CaseCollection([already_erroneous, ok]), {'a': _set_variant('a')}
            )

        by_tag = {c.scenario.tag: c for c in result.cases}
        self.assertEqual('multiple people', by_tag['rejected'].error)
        self.assertIsNone(by_tag['rejected'].variants)
        self.assertIsNone(by_tag['ok'].error)
        self.assertIn('a', by_tag['ok'].variants)

    def test_no_variant_pipelines_returns_cases_unchanged(self):
        case = _case('main')

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            result = _apply_variant_pipelines(CaseCollection([case]), {})

        self.assertEqual(1, len(result.cases))
        self.assertIsNone(result.cases[0].variants)
