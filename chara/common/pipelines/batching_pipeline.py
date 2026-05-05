from .cases import TCase, ICasePipeline, CaseCollection, CaseRepetition
from ..architecture import Chara
from typing import Generic, Callable


class BatchingPipeline(Generic[TCase]):
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 selector: Callable[[list[CaseRepetition.Summary[TCase]]], list[TCase]],
                 max_attempts: int|None = None
                 ):
        self.inner_pipeline = inner_pipeline
        self.selector = selector
        self.max_attempts = max_attempts

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        field_id = Chara.call(CaseRepetition.create_field)('batch')
        cases = CaseRepetition.prepare(field_id, cases)

        results: list[CaseCollection[TCase]] = []
        index = 0
        while True:
            if index >= self.max_attempts:
                break
            index += 1

            rep = CaseRepetition.parse(field_id, cases, results)

            selection = self.selector(rep)
            if len(selection) == 0:
                break

            result = Chara.call(self.inner_pipeline)(CaseCollection(selection).clone())
            results.append(result)

        rep = CaseRepetition.parse(field_id, cases, results)
        final_result = []
        for item in rep:
            final_result.extend(item.successes)
        return CaseCollection(final_result)






