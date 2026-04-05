from chara.common import ICache, FileCache, logger, ListCache
from ..common import ParaphraseRecord, ParaphraseCache, ParaphraseCase
from .case_builder import CaseBuilder
from .stats_builder import build_statistics, add_prior_result, sort_statistics, ParaphraseStats
from pathlib import Path
from .uploading import upload
from typing import Callable
from dataclasses import dataclass

@dataclass
class UtteranceParaphrasesCache:
    stats_before: ParaphraseStats
    stats_after: ParaphraseStats


class UtteranceParaphrasesCache(ICache[list[ParaphraseRecord]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.cases = FileCache[list[ParaphraseCase]]()
        self.stats_before = FileCache[list[ParaphraseStats]]()
        self.batches = ListCache[ParaphraseCache, list[ParaphraseRecord]](ParaphraseCache)
        self.stats_after = FileCache[list[ParaphraseStats]]()


class UtteranceParaphrasePipeline:
    def __init__(self,
                 builder: CaseBuilder,
                 paraphrase: Callable[[ParaphraseCache, list[ParaphraseCase]], None],
                 batches_count: int,
                 templates_in_batch: int = 20
        ):
        self.builder = builder
        self.paraphrase = paraphrase
        self.templates_in_batch = templates_in_batch
        self.batches_count = batches_count


    def __call__(self, cache: UtteranceParaphrasesCache):
        @logger.phase(cache.cases, "Building cases")
        def _():
            cases = self.builder.create_cases()
            cache.cases.write(cases)

        @logger.phase(cache.stats_before, "Building cases and computing statistics with usage data")
        def _():
            cases = cache.cases.read()
            stats = build_statistics(cases)
            cache.stats_before.write(stats)

        @logger.phase(cache.batches, "Running paraphrasing")
        def _():
            results = []
            for i in range(self.batches_count):
                subcache = cache.batches.create_subcache(i)

                @logger.phase(subcache, f"Paraphrasing batch {i}")
                def _():
                    stats = cache.stats_before.read()
                    add_prior_result(stats, results)
                    stats = sort_statistics(stats)
                    cases = [s.case for s in stats[:self.templates_in_batch]]
                    self.paraphrase(subcache, cases)

                results.extend(subcache.read_result())

            cache.batches.write_result(results)

        results = cache.batches.read_result()
        upload(results)

        @logger.phase(cache.stats_after, "Building cases and computing statistics with usage data")
        def _():
            cases = cache.cases.read()
            stats = build_statistics(cases)
            cache.stats_after.write(stats)

        cache.finalize()







