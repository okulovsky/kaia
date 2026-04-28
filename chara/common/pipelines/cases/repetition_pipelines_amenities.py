import copy

from .arch import ICase, CaseCache, TCase
from ...cache import ListCache
from dataclasses import dataclass
from typing import Generic

@dataclass
class RepetitionCaseSummary(Generic[TCase]):
    successes: list[TCase]
    errors: list[str]
    source_case_with_error_message: TCase|None


def collect_results(cases: list[TCase], cache: ListCache[CaseCache[TCase], str]) -> list[RepetitionCaseSummary[TCase]]:
    summaries = [RepetitionCaseSummary([], [], None) for _ in range(len(cases))]
    case_id_field = cache.read_result()
    for attempt in cache.read_subcaches():
        for case in attempt.read_result():
            id = getattr(case, case_id_field)
            summary = summaries[id]
            if case.error:
                summary.errors.append(case.error)
            else:
                summary.successes.append(case)
    for id, summary in enumerate(summaries):
        if len(summary.successes) == 0:
            case = copy.deepcopy(cases[id])
            case.error = "No attempts were successful. Errors are: "+"\n\n".join(summary.errors)
            summary.source_case_with_error_message = case
    return summaries



