from avatar.daemon.paraphrase_service import ParaphraseRecord
from .utterance_paraphrase_case_manager import UtteranceParaphraseCaseManager
from ..common import Paraphrase
from .stats_builder import build_statistics
from .uploading import upload
from chara.common import Chara, BatchingPipeline, CaseRepetition, CaseCollection
from .uterance_paraphrase_case import UtteranceParaphraseCase
from typing import cast


class UtteranceParaphrasePipeline:
    def __init__(self,
                 manager: UtteranceParaphraseCaseManager,
                 settings: Paraphrase.Settings,
                 templates_in_batch: int = 20,
                 paraphrases_upper_count: int|None = None,
                 only_completely_missing: bool = False,
                 max_batch_iterations: int|None = 10,
                 max_case_attempts: int|None = None,
                 ):
        self.manager = manager
        self.settings = settings
        self.templates_in_batch = templates_in_batch
        self.max_batch_iterations = max_batch_iterations
        self.paraphrases_upper_count = paraphrases_upper_count
        self.only_completely_missing = only_completely_missing
        self.max_case_attempts = max_case_attempts

    def _score(self, s: CaseRepetition.Summary[UtteranceParaphraseCase]):
        return max(0, s.case.stats.existing - s.case.stats.seen) + len(s.successes)

    def _selector(self, attempts: list[CaseRepetition.Summary[UtteranceParaphraseCase]]) -> list[UtteranceParaphraseCase]:
        remaining = [s for s in attempts if len(s.successes) == 0]
        if self.only_completely_missing:
            remaining = [s for s in remaining if s.case.stats.existing == 0]
        if self.paraphrases_upper_count is not None:
            remaining = [s for s in remaining if s.case.stats.existing <= self.paraphrases_upper_count]
        if self.max_case_attempts is not None:
            remaining = [s for s in remaining if len(s.errors) < self.max_case_attempts]
        remaining = sorted(remaining, key=self._score)
        return [s.case for s in remaining[:self.templates_in_batch]]


    def __call__(self) -> list[ParaphraseRecord]:
        cases = self.manager.prepare().cases
        cases = cast(CaseCollection[UtteranceParaphraseCase], Paraphrase(cases).prepare()) #Exactly here, otherwise no parsed_template
        cases = CaseCollection(Chara.call(build_statistics)(cases.cases))

        pipeline = Paraphrase.Pipeline(self.settings)
        batcher = BatchingPipeline[UtteranceParaphraseCase](pipeline, self._selector, self.max_batch_iterations)
        result = batcher(cases)

        records = self.manager.apply(result.successes)

        upload(records)
        return records
