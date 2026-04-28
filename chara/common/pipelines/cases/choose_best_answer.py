import uuid
from copy import deepcopy
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from ..logger_definition import logger
from .arch import ICase, ICasePipeline, CaseCache, safe_id
from ...cache import ICache, ListCache
from .repetition_pipelines_amenities import collect_results

class IVotingCase(ABC, ICase):
    @abstractmethod
    def get_result_fingerprint(self) -> str:
        pass

TCase = TypeVar('TCase', bound=IVotingCase)

class ChooseBestAnswerPipeline:
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 poll_size: int = 3
                 ):
        self.inner_pipeline = inner_pipeline
        self.poll_size = poll_size

    def __call__(self, cache: CaseCache[TCase], cases: list[TCase]) -> None:
        attempts_cache: ListCache[CaseCache[TCase], str] = cache.create_subcache('attempts', lambda: ListCache(CaseCache))

        @logger.phase(attempts_cache)
        def _():
            case_id_field = '_choose_best_answer_case_id_'+safe_id()

            for i in range(self.poll_size):
                subcache = attempts_cache.create_subcache(i)

                active_cases = []
                for index, case in enumerate(cases):
                    case = deepcopy(case)
                    setattr(case, case_id_field, index)
                    active_cases.append(case)

                @logger.phase(subcache)
                def __():
                    self.inner_pipeline(subcache, active_cases)

            attempts_cache.write_result(case_id_field)

        summaries = collect_results(cases, attempts_cache)
        result = []
        for summary in summaries:
            if summary.source_case_with_error_message is not None:
                result.append(summary.source_case_with_error_message)
                continue
            fingerprint_to_candidates = {}
            for case in summary.successes:
                fingerprint = case.get_result_fingerprint()
                if fingerprint not in fingerprint_to_candidates:
                    fingerprint_to_candidates[fingerprint] = []
                fingerprint_to_candidates[fingerprint].append(case)
            best_fingerprint = min(fingerprint_to_candidates, key=lambda fp: (-len(fingerprint_to_candidates[fp]), fp))
            result.append(fingerprint_to_candidates[best_fingerprint][0])

        cache.write_result(result)




