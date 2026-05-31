import json
from brainbox import ISelfManagingDecider, BrainBox, File
from uuid import uuid4
from chara.voice_clone.distillation.dataset.prepare_sententes import prepare_sentences
from chara import Chara, Language
from unittest import TestCase


from chara.voice_clone.distillation.dataset import Corpus
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


class PrepareSentencesTestCase(TestCase):
    def test_prepare_sentences(self):
        with Loc.create_test_folder() as folder:
            #folder = Path(__file__).parent/'cache';
            with BrainBox.Api.serverless_test([PhonemizerMock()]) as api:
                Chara.Apis.brainbox_api = api
                Chara.start(folder)
                dataset = [
                    "First sentence",
                    "Second sentence",
                    "Third sentence"
                ]
                corpus = Corpus([], 2)
                result = Chara.call(prepare_sentences)(dataset, corpus, Language.English())
                self.assertEqual(
                    {'584912489fafd32db9b9': 'First sentence',
                     'b592e5fe07c84d078a13': 'Second sentence',
                     '7b8dc614edd82ca59a9f': 'Third sentence'},
                    result.id_to_sentence
                )
                self.assertEqual(
                    {'r': 2, 'e': 10, 'c': 4, 'o': 1},
                    result.rejected_phonemes
                )


