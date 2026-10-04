import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from brainbox.deciders import Chroma, Collector, WhisperKenLM
from chara.common import Chara
from ..kenlm_training import KenLMTrainingPipeline


@dataclass
class NluLanguageStats:
    texts: int = 0
    text_intent: float = 0
    text_intent_at_threshold: float = 0
    voices: int = 0
    wer: float | None = None
    voice_intent: float | None = None
    voice_intent_at_threshold: float | None = None


@dataclass
class NluTrainingReport:
    distance_threshold: float
    languages: dict[str, NluLanguageStats] = field(default_factory=dict)
    transcriptions: list[dict] = field(default_factory=list)

    def __str__(self):
        def pct(value):
            return '-' if value is None else f'{value:.1%}'
        lines = [f'{"":4} {"texts":>6} {"intent":>7} {"@thr":>7} {"voices":>7} {"WER":>7} {"intent":>7} {"@thr":>7}']
        for language, s in self.languages.items():
            lines.append(
                f'{language:4} {s.texts:>6} {pct(s.text_intent):>7} {pct(s.text_intent_at_threshold):>7} '
                f'{s.voices:>7} {pct(s.wer):>7} {pct(s.voice_intent):>7} {pct(s.voice_intent_at_threshold):>7}'
            )
        lines.append(f'@thr: the nearest neighbor is also closer than {self.distance_threshold}')
        return '\n'.join(lines)


class NluTrainingPipeline:
    """
    Trains the models of NluRecognitionSetup on the BrainBox it is connected to:
    KenLM for WhisperKenLM and the intent index for Chroma.

    First the models are trained without a held-out part of the dataset and evaluated on it,
    then they are retrained on the whole dataset into the places NluRecognitionSetup reads from.
    The evaluation index is a separate Chroma collection, so the deployed index is never touched by it.
    """
    EVALUATION_COLLECTION = 'nlu-evaluation'

    def __init__(self,
                 kenlm_weight: float = 0.5,
                 beams: int = 5,
                 languages: tuple[str, ...] | None = ('en', 'de', 'ru'),
                 distance_threshold: float = 0.18,
                 test_share: float = 0.1,
                 voices_per_language: int | None = 100,
                 seed: int = 0,
                 ):
        self.kenlm_weight = kenlm_weight
        self.beams = beams
        self.languages = languages
        self.distance_threshold = distance_threshold
        self.test_share = test_share
        self.voices_per_language = voices_per_language
        self.seed = seed

    def __call__(self, text_dataset: list[dict], voice_samples: list[dict] | None = None) -> NluTrainingReport:
        """
        text_dataset: records with `text`, `intent` and `language`, as produced by TextDatasetPipeline.
        voice_samples: records with `file` (path to the audio) and `text`, the text being one of text_dataset.
        """
        text_to_record = {}
        for record in text_dataset:
            text_to_record.setdefault(record['text'], record)

        @Chara.phase
        def split():
            return self._split(text_to_record, voice_samples or [])

        train, test, voices = split

        @Chara.phase
        def evaluation_lm():
            Chara.call(KenLMTrainingPipeline())([r['text'] for r in train])

        @Chara.phase
        def evaluation_index():
            Chara.Apis.brainbox_api.execute(Chroma.new_task().train(
                _utterances(train), collection_name=self.EVALUATION_COLLECTION
            ))

        @Chara.phase
        def transcriptions():
            return self._run_all([
                WhisperKenLM.new_task().transcribe(
                    file=v['file'], weight=self.kenlm_weight, beams=self.beams,
                    languages=list(self.languages) if self.languages else None,
                )
                for v in voices
            ])

        @Chara.phase
        def text_neighbors():
            return self._find_neighbors([r['text'] for r in test])

        @Chara.phase
        def voice_neighbors():
            return self._find_neighbors([str(t) for t in transcriptions])

        report = self._report(test, text_neighbors, voices, transcriptions, voice_neighbors, text_to_record)

        @Chara.phase
        def deployment():
            records = list(text_to_record.values())
            Chara.call(KenLMTrainingPipeline())([r['text'] for r in records])
            Chara.Apis.brainbox_api.execute(Chroma.new_task().train(_utterances(records)))

        return report

    def _split(self, text_to_record: dict[str, dict], voice_samples: list[dict]):
        rnd = random.Random(self.seed)
        by_language = defaultdict(list)
        for sample in voice_samples:
            record = text_to_record.get(sample['text'])
            if record is not None:
                by_language[record['language']].append(sample)
        voices = []
        for language in sorted(by_language):
            samples = by_language[language]
            if self.voices_per_language is not None and len(samples) > self.voices_per_language:
                samples = rnd.sample(samples, self.voices_per_language)
            voices.extend(samples)

        # The split is by text: a voiced text must not get into the index or the language model,
        # otherwise the evaluation measures memorization.
        test_texts = {v['text'] for v in voices}
        rest = sorted(t for t in text_to_record if t not in test_texts)
        test_texts.update(rnd.sample(rest, int(len(rest) * self.test_share)))
        train = [r for t, r in text_to_record.items() if t not in test_texts]
        test = [r for t, r in text_to_record.items() if t in test_texts]
        return train, test, voices

    def _run_all(self, tasks: list) -> list:
        if len(tasks) == 0:
            return []
        builder = Collector.TaskBuilder()
        for index, task in enumerate(tasks):
            builder.append(task, dict(index=index))
        results = Chara.Apis.brainbox_api.execute(builder.to_collector_pack('to_array'))
        return [item['result'] for item in sorted(results, key=lambda item: item['tags']['index'])]

    def _find_neighbors(self, texts: list[str]) -> list[list[dict]]:
        return self._run_all([
            Chroma.new_task().find_neighbors(text=text, k=1, collection_name=self.EVALUATION_COLLECTION)
            for text in texts
        ])

    def _report(self, test, text_neighbors, voices, transcriptions, voice_neighbors, text_to_record) -> NluTrainingReport:
        report = NluTrainingReport(self.distance_threshold)
        languages = sorted({r['language'] for r in test})
        for language in languages + ['all']:
            report.languages[language] = NluLanguageStats()

        text_counts = defaultdict(lambda: [0, 0, 0])
        for record, neighbors in zip(test, text_neighbors):
            hit, hit_at_threshold = self._hit(record['intent'], neighbors)
            for key in (record['language'], 'all'):
                c = text_counts[key]
                c[0] += 1; c[1] += hit; c[2] += hit_at_threshold

        voice_counts = defaultdict(lambda: [0, 0, 0, 0, 0])
        for voice, transcription, neighbors in zip(voices, transcriptions, voice_neighbors):
            record = text_to_record[voice['text']]
            hit, hit_at_threshold = self._hit(record['intent'], neighbors)
            errors, words = _word_errors(voice['text'], str(transcription))
            report.transcriptions.append(dict(
                file=voice['file'], language=record['language'], reference=voice['text'],
                transcription=transcription, intent=record['intent'], neighbors=neighbors,
            ))
            for key in (record['language'], 'all'):
                c = voice_counts[key]
                c[0] += 1; c[1] += hit; c[2] += hit_at_threshold; c[3] += errors; c[4] += words

        for key, stats in report.languages.items():
            n, hit, hit_at_threshold = text_counts[key]
            stats.texts = n
            stats.text_intent = hit / n if n else 0
            stats.text_intent_at_threshold = hit_at_threshold / n if n else 0
            n, hit, hit_at_threshold, errors, words = voice_counts[key]
            stats.voices = n
            if n:
                stats.wer = errors / words if words else 0
                stats.voice_intent = hit / n
                stats.voice_intent_at_threshold = hit_at_threshold / n
        return report

    def _hit(self, intent: str, neighbors: list[dict]) -> tuple[bool, bool]:
        if not neighbors or neighbors[0]['intent'] != intent:
            return False, False
        return True, neighbors[0]['distance'] <= self.distance_threshold


def load_nlu_datasets(folder: Path) -> tuple[list[dict], list[dict]]:
    """
    Reads the datasets in the layout of chara/nlu/datasets/run_*.py:
    `text-dataset.json` and, optionally, the voiced samples `to_zip/samples.json` with their audio files.
    """
    text_dataset_path = folder / 'text-dataset.json'
    if not text_dataset_path.is_file():
        raise FileNotFoundError(f"{text_dataset_path} is not found, create it with chara/nlu/datasets/run_text_dataset.py")
    text_dataset = json.loads(text_dataset_path.read_text())
    voice_samples = []
    samples_path = folder / 'to_zip' / 'samples.json'
    if samples_path.is_file():
        for sample in json.loads(samples_path.read_text()):
            voice_samples.append(dict(file=str(samples_path.parent / sample['filename']), text=sample['text']))
    return text_dataset, voice_samples


def _utterances(records: list[dict]) -> list[dict]:
    return [dict(text=r['text'], intent=r['intent'], language=r['language']) for r in records]


_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)


def _words(text: str) -> list[str]:
    return _PUNCTUATION.sub(' ', text.lower().replace('ё', 'е')).split()


def _word_errors(reference: str, hypothesis: str) -> tuple[int, int]:
    r, h = _words(reference), _words(hypothesis)
    previous = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        current = [i] + [0] * len(h)
        for j in range(1, len(h) + 1):
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (r[i - 1] != h[j - 1]))
        previous = current
    return previous[-1], len(r)
