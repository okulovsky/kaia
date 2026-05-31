import time
from dataclasses import dataclass
from functools import partial
from unittest import TestCase
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

    def set_annotation(self, annotation):
        self.annotation = annotation


class AnnotationTestCase(TestCase):
    def find_label(self, label, elements):
        for element in elements:
            if isinstance(element, dict):
                if 'label' in element and element['label'] == label:
                    return
                if (
                        'value' in element
                        and isinstance(element['value'], dict)
                        and 'label' in element['value']
                        and element['value']['label'] == label
                ):
                    return
        self.fail(f"Element {label} not found in {elements}")

    def test_annotation(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            cases = [MyCase('record_1', 'Record 1'), MyCase('record_2', 'Record 2'), MyCase('record_3', 'Record 3')]
            annotator = TextLabelAnnotator(lambda c: c.text, TextLabelAnnotator.Settings(('Yes', 'No'), 'Skip'))

            with Fork(partial(annotator.run, cases=cases, folder=folder)):
                ApiUtils.wait_for_reply("http://127.0.0.1:7860/", 5)
                client = Client("http://127.0.0.1:7860/")

                result = client.predict(api_name="/on_load")
                self.find_label('Record 1', result)

                result = client.predict('Skip', api_name='/on_button')
                self.find_label('Record 2', result)

                result = client.predict('Yes', api_name='/on_button')
                self.find_label('Record 3', result)

                result = client.predict('Yes', api_name='/on_button')
                self.find_label('Record 1', result)

                result = client.predict('Undo', api_name='/on_undo')
                self.find_label('Record 3', result)

                result = client.predict('No', api_name='/on_button')
                self.find_label('Record 1', result)

                result = client.predict('Yes', api_name='/on_button')
                self.find_label('ALL DONE', result)

            cache = LabelAnnotationCache(folder)
            self.assertTrue(cache.ready)
            data = cache.get_result()
            self.assertDictEqual({'record_2': 'Yes', 'record_3': 'No', 'record_1': 'Yes'}, data)
