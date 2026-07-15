import json
from brainbox import ISelfManagingDecider, BrainBox, File
from uuid import uuid4
from unittest import TestCase

from chara.voice_clone.distillation.dataset import Corpus, PreviewDatasetPipeline
from chara import Chara, Language
from foundation_kaia.misc import Loc


class PhonemizerMock(ISelfManagingDecider):
    def get_name(self):
        return "EspeakPhonemizer"

    def phonemize_to_file(self, text: list[str], language: str = 'en-us', stress: bool = False):
        result = []
        for line in text:
            line_phonemization = []
            for word in line.split(' '):
                word_phonemization = list(word.lower())
                line_phonemization.append(word_phonemization)
            result.append(line_phonemization)
        return File(str(uuid4()), json.dumps(result).encode('utf-8'))


class PreviewDatasetPipelineTestCase(TestCase):
    def test_preview_dataset_pipeline(self):
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([PhonemizerMock()]) as api:
                Chara.Apis.brainbox_api = api
                Chara.start(folder)
                dataset = [
                    "First sentence",
                    "Second sentence",
                    "Third sentence"
                ]
                corpus = Corpus([], 2)
                pipeline = PreviewDatasetPipeline(corpus, Language.English())
                dataset_path = Chara.call(pipeline)(dataset)

                self.assertEqual(folder / 'dataset.jsonlines', dataset_path)
                self.assertTrue(dataset_path.exists())
                self.assertTrue((folder / 'report.html').exists())

                rows = {}
                with open(dataset_path, 'r') as file:
                    for line in file:
                        row = json.loads(line)
                        rows[row['id']] = row['text']

                self.assertEqual(
                    {'584912489fafd32db9b9': 'First sentence',
                     'b592e5fe07c84d078a13': 'Second sentence',
                     '7b8dc614edd82ca59a9f': 'Third sentence'},
                    rows
                )
