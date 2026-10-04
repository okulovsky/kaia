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
        # Successes only, as in RepeatUntilDone and ChooseBestAnswer: a case that arrived
        # already broken should not be handed to the inner pipeline, and it must not be
        # counted twice when cases.errors is added back at the end.
        tracker = CaseRepetition.Tracker(
            self.inner_pipeline, field_name, CaseCollection(cases.successes))

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
            # A case the inner pipeline failed comes back carrying its error, as it does from
            # RepeatUntilDone and ChooseBestAnswer. `error_on_empty` stays False because
            # stopping early is what this pipeline is for: a case the selector never handed
            # out was not attempted, and an unattempted case is not a failed one.
            error = summary.create_error_case_if_no_successes(False)
            if error is not None:
                final_result.append(error)
            else:
                final_result.extend(summary.successes)
        return CaseCollection(final_result, cases.errors)
