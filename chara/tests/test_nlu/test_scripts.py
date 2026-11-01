import json
import os
from unittest import TestCase
from unittest.mock import patch
from brainbox import BrainBox
from brainbox.deciders import Ollama
from brainbox.deciders.text.llama_lora_sft_trainer.api import TrainingRun
from brainbox.framework import ISelfManagingDecider
from foundation_kaia.marshalling import FileLike
from foundation_kaia.misc import Loc
from chara.common import Chara
from chara.nlu.scripts import create_negatives, train_ultimate_nlu
from chara.nlu.scripts.common import training_folder
from chara.nlu.nlu_training import NluTrainingReport
from chara.nlu.ner_training import NerTrainingReport
from chara.nlu.slm_training.stats import TrainingRunStats


class OllamaMock(ISelfManagingDecider):
    """Every answer is a new list of phrases, the first phrase repeats in all of them; numbers and translations as small models add them"""
    def __init__(self):
        self.calls = 0

    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: Ollama.Options | None = None, image: FileLike | None = None) -> str:
        self.calls += 1
        return f'- 1. what a day (was für ein Tag)\n- phrase {self.calls}a\n- "phrase {self.calls}b" (Satz)'


class TrainingMock:
    def __init__(self, report):
        self.report = report
        self.arguments = None

    def __call__(self, *args):
        self.arguments = args
        return self.report


class CreateNegativesTestCase(TestCase):
    def test_runs_accumulate(self):
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                create_negatives('mock', ('en', 'ru'), 2, folder)
                path = create_negatives('mock', ('en', 'ru'), 2, folder)
            runs = list((folder/'negatives').iterdir())
            phrases = path.read_text().splitlines()
        self.assertEqual(2, len(runs))
        self.assertEqual('what a day', phrases[0])
        self.assertEqual(1, phrases.count('what a day'))
        self.assertIn('phrase 1b', phrases)
        # 2 runs, 2 languages, 2 batches, 2 new phrases in each answer
        self.assertEqual(1 + 2 * 2 * 2 * 2, len(phrases))

    def test_unfinished_run_is_resumed(self):
        with Loc.create_test_folder() as folder:
            unfinished = folder/'negatives'/'$2000-01-01T00:00:00'
            os.makedirs(unfinished)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                create_negatives('mock', ('en',), 1, folder)
            runs = list((folder/'negatives').iterdir())
            has_result = Chara.from_folder(unfinished).has_result
        self.assertEqual([unfinished], runs)
        self.assertTrue(has_result)


class TrainUltimateNluTestCase(TestCase):
    def test_negatives_are_trained_and_fingerprinted(self):
        dataset = [dict(text='what time is it', intent='time', language='en', values=[])]
        nlu = TrainingMock(NluTrainingReport(0.18))
        ner = TrainingMock(NerTrainingReport(TrainingRunStats(TrainingRun('model', 'nlu-slots', 'guid'), []), 0))
        with Loc.create_test_folder() as folder:
            (folder/'dataset.json').write_text(json.dumps(dataset))
            without_negatives = training_folder(folder)
            (folder/'negatives.txt').write_text('nice weather\n\nwhere is my cup\n')
            with_negatives = training_folder(folder)
            with patch('chara.nlu.scripts.train_ultimate_nlu.NluTrainingPipeline', lambda: nlu), \
                 patch('chara.nlu.scripts.train_ultimate_nlu.NerTrainingPipeline', lambda: ner):
                train_ultimate_nlu(folder)
            trained_in = list((folder/'$training').iterdir())
        self.assertNotEqual(without_negatives, with_negatives)
        self.assertEqual([with_negatives], trained_in)
        self.assertEqual((dataset,), nlu.arguments)
        self.assertEqual((dataset, ['nice weather', 'where is my cup']), ner.arguments)
