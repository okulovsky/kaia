import json
from unittest import TestCase
from brainbox import BrainBox
from brainbox.deciders import Collector
from foundation_kaia.misc import Loc
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline
from chara.nlu.nlu_pipeline import NluDatasetStore, NluPipeline
from chara.tests.test_nlu.test_nlu_training import WhisperKenLMMock, ChromaMock


def _record(text: str, intent: str = 'time') -> dict:
    return dict(text=text, intent=intent, values=[], language='en')


class FakeGenerator:
    """Generates 10 new phrases on each call, as the LLM does with sampling"""
    def __init__(self, fail_first: bool = False):
        self.calls = 0
        self.fail_first = fail_first

    def __call__(self) -> list[dict]:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise ValueError("The LLM is down")
        return [_record(f'what time is it {self.calls}-{i}') for i in range(10)]


class NluPipelineTestCase(TestCase):
    def setUp(self):
        self.whisper, self.chroma = WhisperKenLMMock(), ChromaMock()

    def create(self, folder, generator) -> NluPipeline:
        store = NluDatasetStore(folder / 'datasets')
        return NluPipeline(store, folder / 'cache', generator, NluTrainingPipeline(test_share=0.2, voices_per_language=1))

    def run_api(self, action):
        with BrainBox.Api.serverless_test([self.whisper, self.chroma, Collector()]) as api:
            Chara.Apis.brainbox_api = api
            return action()

    def test_rounds_accumulate(self):
        with Loc.create_test_folder() as folder:
            pipeline = self.create(folder, FakeGenerator())
            self.assertEqual([1, 2], [pipeline.generate_round(), pipeline.generate_round()])
            self.assertEqual(20, len(pipeline.store.read()))
            self.assertEqual([1, 2], pipeline.store.rounds())

    def test_legacy_dataset_becomes_round_0(self):
        with Loc.create_test_folder() as folder:
            (folder / 'datasets').mkdir()
            (folder / 'datasets/text-dataset.json').write_text(json.dumps([_record('legacy'), _record('legacy')]))
            pipeline = self.create(folder, FakeGenerator())
            self.assertEqual(1, pipeline.generate_round())
            self.assertEqual([0, 1], pipeline.store.rounds())
            dataset = pipeline.store.read()
            self.assertEqual(12, len(dataset))  # repeated phrases are kept
            self.assertEqual(2, sum(r['text'] == 'legacy' for r in dataset))

    def test_failed_round_continues(self):
        with Loc.create_test_folder() as folder:
            generator = FakeGenerator(fail_first=True)
            pipeline = self.create(folder, generator)
            with self.assertRaises(ValueError):
                pipeline.generate_round()
            self.assertEqual(1, pipeline.generate_round())
            self.assertEqual([1], pipeline.store.rounds())

    def test_training_reruns_only_when_dataset_changes(self):
        with Loc.create_test_folder() as folder:
            pipeline = self.create(folder, FakeGenerator())
            pipeline.generate_round()
            report = self.run_api(pipeline.train)
            self.assertEqual(10, report.records)
            self.assertEqual(10, len(self.chroma.collections[None]))
            trainings = len(self.whisper.corpora)

            self.run_api(pipeline.train)
            self.assertEqual(trainings, len(self.whisper.corpora))

            pipeline.generate_round()
            report = self.run_api(pipeline.train)
            self.assertEqual(20, report.records)
            self.assertEqual(20, len(self.chroma.collections[None]))
            self.assertGreater(len(self.whisper.corpora), trainings)

    def test_no_generator(self):
        with Loc.create_test_folder() as folder:
            pipeline = self.create(folder, None)
            with self.assertRaises(ValueError):
                pipeline.generate_round()
