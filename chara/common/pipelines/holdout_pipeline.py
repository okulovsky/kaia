from .cases import TCase, ICasePipeline, CaseCollection
from ..architecture import Chara
from typing import Generic, Callable


class HoldoutPipeline(Generic[TCase]):
    def __init__(self,
                 inner: ICasePipeline[TCase],
                 holdout_condition: Callable[[TCase], bool]
                 ):
        self.inner = inner
        self.holdout_condition = holdout_condition

    def __call__(self, cases:CaseCollection[TCase]) -> CaseCollection[TCase]:
        holdout = []
        propagate = []
        for case in cases.successes:
            if self.holdout_condition(case):
                holdout.append(case)
            else:
                propagate.append(case)

        after_pipeline = Chara.call(self.inner)(CaseCollection(propagate))

        return CaseCollection(
            holdout,
            after_pipeline,
            cases.errors
        )


