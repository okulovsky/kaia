from ...architecture import Chara
from ..cases import TCase, CaseCollection, ICasePipeline
from .repetition import CaseRepetition


class RepeatUntilDonePipeline:
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 attempts: int = 5,
                 ):
        self.inner_pipeline = inner_pipeline
        self.attempts = attempts

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        field_name = Chara.call(CaseRepetition.create_field)('repeat_until_done')
        tracker = CaseRepetition.Tracker(self.inner_pipeline, field_name, CaseCollection(cases.successes))

        for i in range(self.attempts):
            remaining = [s.case for s in tracker.get_state() if len(s.successes) == 0]
            if not remaining:
                break
            tracker.iteration(remaining)

        result = []
        for summary in tracker.get_state():
            err = summary.create_error_case_if_no_successes(True)
            if err:
                result.append(err)
            else:
                result.append(summary.successes[0])

        return CaseCollection(result, cases.errors)
