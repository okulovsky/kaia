import time
from dataclasses import dataclass
from functools import partial
from unittest import TestCase

from chara import AnnotationPipeline, CaseCollection, Chara
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc
from foundation_kaia.marshalling import ApiUtils
from gradio_client import Client
from chara.common.pipelines.annotation import TextLabelAnnotator, LabelAnnotationCache
from chara.common.pipelines.annotation.core import IAnnotationCase


@dataclass
class MyCase(IAnnotationCase):
    id: str
    text: str
    annotation: str | None = None

    def get_id(self) -> str:
        return self.id


def _mock(case: MyCase):
    return 'Yes' if '3' in case.text else 'No'


class MockAnnotationTestCase(TestCase):
    def test_mock_annotation(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            Chara.start(folder)
            cases = [MyCase('record_1', 'Record 1'), MyCase('record_2', 'Record 2'), MyCase('record_3', 'Record 3')]
            annotator = TextLabelAnnotator(
                lambda c: c.text,
                TextLabelAnnotator.Settings(('Yes', 'No'), 'Skip'),
                mock_annotation=_mock
            )
            pipe = AnnotationPipeline(annotator, 'annotation')
            result = Chara.call(pipe.__call__)(CaseCollection(cases)).cases
            self.assertEqual(3, len(result))
            self.assertEqual('No', result[0].annotation)
            self.assertEqual('No', result[1].annotation)
            self.assertEqual('Yes', result[2].annotation)
