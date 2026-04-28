from dataclasses import dataclass
from .stats_builder import ParaphraseStats
from chara.common import *
from avatar.daemon.paraphrase_service import ParaphraseRecord
from pathlib import Path
from .utterance_paraphrase_case_manager import UtteranceParaphraseCaseManager
from ..common import ParaphrasePipelineSettings, ParaphraseCache, ParaphrasePipeline
from .stats_builder import build_statistics, add_prior_result, sort_statistics
from .uterance_paraphrase_case import UtteranceParaphraseCase
from .uploading import upload


class UtteranceParaphrasesCache(ICache[list[ParaphraseRecord]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.stats_before = FileCache[list[ParaphraseStats]]()
        self.batches = ListCache[ParaphraseCache, list[ParaphraseRecord]](ParaphraseCache)
        self.stats_after = FileCache[list[ParaphraseStats]]()


class UtteranceParaphrasePipeline:
    def __init__(self,
                 manager: UtteranceParaphraseCaseManager,
                 settings: ParaphrasePipelineSettings,
                 batches_count: int,
                 templates_in_batch: int = 20,
                 only_completely_missing: bool = False
        ):
        self.manager = manager
        self.settings = settings
        self.templates_in_batch = templates_in_batch
        self.batches_count = batches_count
        self.only_completely_missing = only_completely_missing


    def __call__(self, cache: UtteranceParaphrasesCache):
        cases = self.manager.prepare()

        @logger.phase(cache.stats_before, "Building cases and computing statistics with usage data")
        def _():
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
                    stats = sort_statistics(stats, self.only_completely_missing)
                    stats = stats[:self.templates_in_batch]
                    logger.info(f"At iteration {i}, {len(stats)} are selected:")
                    for j, s in enumerate(stats):
                        logger.info(f"#{j}, existing {s.existing}, seen {s.seen}: {s.case.parsed_template.representation}")

                    if len(stats) == 0:
                        subcache.write_result([])

                    cases = [s.case for s in stats]
                    pipeline = ParaphrasePipeline(self.settings)
                    pipeline(subcache, cases)

                addition: list[UtteranceParaphraseCase] = subcache.read_result()
                addition_records = self.manager.apply(addition)
                if len(addition_records) == 0:
                    break
                results.extend(addition_records)

            cache.batches.write_result(results)

        results = cache.batches.read_result()
        upload(results)

        @logger.phase(cache.stats_after, "Building cases and computing statistics with usage data")
        def _():
            cases = self.manager.prepare()
            stats = build_statistics(cases)
            cache.stats_after.write(stats)

        cache.finalize()







