from copy import deepcopy
from ..architecture import Chara
from .cases import TCase, CaseCollection, CaseRepetition, ICasePipeline


class RepeatUntilDonePipeline:
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 attempts: int = 5,
                 ):
        self.inner_pipeline = inner_pipeline
        self.attempts = attempts


    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        field_id = Chara.call(CaseRepetition.create_field)('repeat_until_done')
        cases = CaseRepetition.prepare(field_id, cases)
        active_cases = {getattr(c, field_id): c for c in cases.successes}

        attempts = []
        for i in range(self.attempts):
            inner_cases = CaseCollection(deepcopy(c) for c in active_cases.values())
            result = Chara.call(self.inner_pipeline)(inner_cases)
            attempts.append(result)
            for reply in result.successes:
                del active_cases[getattr(reply, field_id)]
            if len(active_cases) == 0:
                break

        summaries = CaseRepetition.parse(field_id, cases, attempts)
        result = []
        for summary in summaries:
            err = summary.create_error_case_if_no_successes(True)
            if err:
                result.append(err)
            else:
                result.append(summary.successes[0])

        return CaseCollection(result, cases.errors)