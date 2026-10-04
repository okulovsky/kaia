from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector
from foundation_kaia.marshalling import FileLike
from foundation_kaia.misc import Loc
from chara.common import Chara
from chara.nlu.nlu_training import NluTrainingPipeline


TEXT_DATASET = (
    [dict(text=f'what time is it {i}', intent='time', language='en') for i in range(10)]
    + [dict(text=f'stell den timer {i}', intent='timer', language='de') for i in range(10)]
)

VOICE_SAMPLES = [
    dict(file='what time is it 0', text='what time is it 0'),
    dict(file='stell den timer 0', text='stell den timer 0'),
    dict(file='not in the dataset', text='not in the dataset'),
]


class WhisperKenLMMock(ISelfManagingDecider):
    def __init__(self):
        self.corpora = []

    def get_name(self):
        return 'WhisperKenLM'

    def train_lm(self, corpus: str) -> None:
        self.corpora.append(corpus)

    def transcribe(self, file: FileLike, weight: float = 0.5, beams: int = 5, languages: list[str] | None = None) -> str:
        # Files of the test are named after their text
        return str(file)


class ChromaMock(ISelfManagingDecider):
    def __init__(self):
        self.collections = {}

    def get_name(self):
        return 'Chroma'

    def train(self, utterances: list[dict], collection_name: str | None = None) -> None:
        self.collections[collection_name] = utterances

    def find_neighbors(self, text: str, k: int = 5, collection_name: str | None = None) -> list[dict]:
        intent = 'time' if text.startswith('what') else 'timer'
        return [dict(text=text, intent=intent, distance=0.1)]

    def get_vector(self, text: str) -> list[float]:
        return [0.0]


class NluTrainingPipelineTestCase(TestCase):
    def run_pipeline(self, whisper, chroma, voice_samples):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([whisper, chroma, Collector()]) as api:
                Chara.Apis.brainbox_api = api
                pipeline = NluTrainingPipeline(test_share=0.2, voices_per_language=1)
                return Chara.call(pipeline)(TEXT_DATASET, voice_samples)

    def test_evaluates_on_held_out_texts_and_deploys_on_all(self):
        whisper, chroma = WhisperKenLMMock(), ChromaMock()
        report = self.run_pipeline(whisper, chroma, VOICE_SAMPLES)

        evaluation_corpus, deployment_corpus = whisper.corpora
        evaluation_index = chroma.collections[NluTrainingPipeline.EVALUATION_COLLECTION]
        held_out = {t['reference'] for t in report.transcriptions}
        self.assertEqual({'what time is it 0', 'stell den timer 0'}, held_out)
        for text in held_out:
            self.assertNotIn(text, evaluation_corpus.split('\n'))
            self.assertNotIn(text, [u['text'] for u in evaluation_index])
        self.assertEqual(len(TEXT_DATASET), len(deployment_corpus.split('\n')))
        self.assertEqual(len(TEXT_DATASET), len(chroma.collections[None]))

        stats = report.languages['all']
        self.assertEqual(2, stats.voices)
        self.assertEqual(0, stats.wer)
        self.assertEqual(1, stats.voice_intent)
        self.assertEqual(1, stats.text_intent)
        self.assertEqual(len(TEXT_DATASET) - len(evaluation_index), stats.texts)

    def test_works_without_voices(self):
        whisper, chroma = WhisperKenLMMock(), ChromaMock()
        report = self.run_pipeline(whisper, chroma, [])

        self.assertEqual(0, report.languages['all'].voices)
        self.assertIsNone(report.languages['all'].wer)
        self.assertEqual(len(TEXT_DATASET), len(chroma.collections[None]))
