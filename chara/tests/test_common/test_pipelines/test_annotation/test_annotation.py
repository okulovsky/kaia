import time
from unittest import TestCase
from chara.common import AnnotationUnit, TextLabelAnnotator, LabelAnnotationCache, ICache
from foundation_kaia.misc import Loc
from dataclasses import dataclass, field
from foundation_kaia.marshalling import ApiUtils
from gradio_client import Client
from collections import OrderedDict

class MyCache(ICache):
    def __init__(self, working_folder):
        super().__init__(working_folder)
        self.cache = LabelAnnotationCache()

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
            cache = MyCache(folder)
            annotaton = OrderedDict(record_1 = 'Record 1', record_2 = 'Record 2', record_3 = 'Record 3')
            annotator = TextLabelAnnotator(annotaton,  TextLabelAnnotator.Settings(('Yes', 'No'),'Skip'))
            annotation_unit = AnnotationUnit(annotator)
            fork = annotation_unit.start(cache.cache)

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

            self.assertTrue(cache.cache.ready)
            data = cache.cache.get_result()
            self.assertDictEqual(
                {'record_2': 'Yes', 'record_3': 'No', 'record_1': 'Yes'},
                data
            )

            annotation_unit.end(fork, cache.cache)

