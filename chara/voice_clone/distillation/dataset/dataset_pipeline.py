from typing import Iterable
from chara import Chara, Language, logger
from .common import AnnotationCase
from .corpus import Corpus
from .prepare_sententes import prepare_sentences
from .algorithm_annotation_step import algorithm_annotation_step

class DatasetPipeline:
    def __init__(self,
                 corpus: Corpus,
                 language: Language,
                 samples_per_batch: int = 100,
                 exit_count: int = 100,
                 banned_words: Iterable[str] = (),
                 ):
        self.corpus = corpus
        self.language = language
        self.samples_per_batch = samples_per_batch
        self.exit_count = exit_count
        self.banned_words = set(banned_words)

    def __call__(self, raw_dataset: Iterable[str]):
        data = Chara.call(prepare_sentences(raw_dataset, self.corpus, self.language))

        annotations: list[AnnotationCase] = []
        while True:
            addition = Chara.call(algorithm_annotation_step)(data, annotations, self.samples_per_batch, self.banned_words)
            annotations.extend(addition)
            ready = [case.text for case in annotations if case.accepted]
            logger.info(f"Available {len(ready)} sentences")
            if len(ready) > self.exit_count:
                return ready

