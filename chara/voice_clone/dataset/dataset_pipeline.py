import pandas as pd
from typing import Iterable
from itertools import tee
from ...common import Language, logger, BrainBoxPipeline
from ...common import ICache, JsonlCache, BrainBoxCache, logger, FileCache, ListCache
from .phonemization import create_phonemization_samples, merge, Phonemization
from .corpus import Corpus
from .algorithm import AlgorithmData, AnnotatedSentence
from .annotation_pipeline import AnnotationPipeline, AnnotationCacheData
from pathlib import Path
from brainbox import BrainBox
from brainbox.deciders import EspeakPhonemizer


class DatasetCache(ICache[list[str]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.source_file_length = FileCache[int](FileCache.Type.Json)
        self.filtered_corpus = JsonlCache[list[str]]()
        self.phonemization = BrainBoxCache[list[str], list[Phonemization]]()
        self.data = FileCache[AlgorithmData]()
        self.annotation_steps = ListCache[AnnotationCacheData, list[AnnotatedSentence]](AnnotationCacheData)

    def export(self) -> list[str]|None:
        results: list[AnnotatedSentence] = []
        for step in self.annotation_steps.read_subcaches():
            if step.ready:
                results.extend(step.read_result())
        return [r.text for r in results if r.accepted]





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

    def _create_phonemization_task(self, case):
        return EspeakPhonemizer.new_task().phonemize_to_file(case, self.language.espeak_name)

    def __call__(self,
                 cache: DatasetCache,
                 raw_dataset: Iterable[str]):
        source_1, source_2 = tee(raw_dataset)

        @logger.phase(cache.source_file_length)
        def _():
            count = 0
            for _ in source_1:
                count += 1
            logger.log(f"{count} sentences in the dataset in the source dataset")
            cache.source_file_length.write(count)


        @logger.phase(cache.filtered_corpus)
        def _():
            self.corpus.create(source_2, cache.filtered_corpus, cache.source_file_length.read())

        lines_count = 0
        packages_count = 0
        for array in cache.filtered_corpus.read():
            lines_count += len(array)
            packages_count += 1
        logger.log(f"{lines_count} sentences in the dataset in {packages_count} packages")
        if lines_count == 0 or packages_count == 0:
            raise ValueError("No lines in the dataset.")

        @logger.phase(cache.phonemization)
        def _():
            unit = BrainBoxPipeline(
                self._create_phonemization_task,
                merge,
            )
            unit.run(cache.phonemization, cache.filtered_corpus.read())

            data = list(cache.phonemization.read_options().select_many(lambda z: z))
            samples_df = create_phonemization_samples(self.language, data)
            logger.log("Reference table:")
            logger.log(samples_df)
            logger.log(list(samples_df.phoneme))
            logger.log(f"{len(data)} sentences are phonemized")

        @logger.phase(cache.data)
        def _():
            cache.data.write(
                AlgorithmData.from_phonemizations(
                    cache.phonemization.read_options().select_many(lambda z: z),
                    self.language
            ))

        data = cache.data.read()
        logger.log(f"{len(data.id_to_sentence)} sentences are available for the algorithm, with {len(data.features.feature.unique())} phonemes")
        logger.log("Example:")
        logger.log(data.features.head(5))
        logger.log("Rejected phonemes:")
        logger.log(pd.Series(data.rejected_phonemes).sort_values(ascending=False))

        annotation_pipeline = AnnotationPipeline(self.samples_per_batch, self.banned_words)

        @logger.phase(cache.annotation_steps)
        def _():
            results = []
            for i in range(100):
                @logger.phase(cache.annotation_steps[i])
                def __():
                    new_results = annotation_pipeline(cache.annotation_steps[i], data, results)
                    cache.annotation_steps[i].write_result(new_results)

                step_results = cache.annotation_steps[i].read_result()
                if len(step_results) == 0:
                    break
                results.extend(step_results)
                ready = sum(1 for t in results if t.accepted)
                if ready >= self.exit_count:
                    break
                logger.log(f"Currently produced {ready} sentences")
            cache.annotation_steps.write_result(results)

        annotation_result = cache.annotation_steps.read_result()
        return [a.text for a in annotation_result if a.accepted]






