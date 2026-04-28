from copy import deepcopy
from typing import Generic
from .arch import TCase, ICasePipeline, CaseCache, safe_id
from ..logger_definition import logger
from ...cache import ListCache
from .repetition_pipelines_amenities import collect_results

class RepeatUntilDonePipeline(ICasePipeline[TCase], Generic[TCase]):
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 attempts: int = 5,
                 ):
        self.inner_pipeline = inner_pipeline
        self.attempts = attempts


    def __call__(self, cache: CaseCache[TCase], cases: list[TCase]):
        active_cases = {i: case for i, case in enumerate(cases)}

        attempts_cache: ListCache[CaseCache[TCase], str] = cache.create_subcache('attempts', lambda: ListCache(CaseCache))

        @logger.phase(attempts_cache)
        def _():
            case_id_field = '_repeat_until_done_case_id_' + safe_id()
            for i in range(self.attempts):
                subcache = attempts_cache.create_subcache(i)

                cases_for_iteration = []
                for index, case in active_cases.items():
                    case = deepcopy(case)
                    setattr(case, case_id_field, index)
                    cases_for_iteration.append(case)

                @logger.phase(subcache)
                def __():
                    self.inner_pipeline(subcache, cases_for_iteration)

                for case in subcache.read_result():
                    if case.error is None:
                        id = getattr(case, case_id_field)
                        del active_cases[id]

                if len(active_cases) == 0:
                    break


            attempts_cache.write_result(case_id_field)

        summaries = collect_results(cases, attempts_cache)
        result = []
        for summary in summaries:
            if summary.source_case_with_error_message:
                result.append(summary.source_case_with_error_message)
            else:
                result.append(summary.successes[0])

        cache.write_result(result)