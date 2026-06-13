from ..cases import TCase, ICasePipeline, CaseCollection
from .repetition import CaseRepetition
from ...architecture import Chara
from typing import Generic, Callable


class BatchingPipeline(Generic[TCase]):
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 selector: Callable[[list[CaseRepetition.Summary[TCase]]], list[TCase]],
                 max_batch_iterations: int|None = None
                 ):
        self.inner_pipeline = inner_pipeline
        self.selector = selector
        self.max_batch_iterations = max_batch_iterations

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        field_name = Chara.call(CaseRepetition.create_field)('batch')
        tracker = CaseRepetition.Tracker(self.inner_pipeline, field_name, cases)

        index = 0
        while True:
            if self.max_batch_iterations is not None and index >= self.max_batch_iterations:
                break
            index += 1

            selection = self.selector(tracker.get_state())
            if len(selection) == 0:
                break

            tracker.iteration(selection)

        final_result = []
        for summary in tracker.get_state():
            final_result.extend(summary.successes)
        return CaseCollection(final_result)
