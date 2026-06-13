from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from ...architecture import Chara
from ..cases import ICase, ICasePipeline, CaseCollection
from .repetition import CaseRepetition


class IVotingCase(ABC, ICase):
    @abstractmethod
    def get_result_fingerprint(self) -> str:
        pass

TCase = TypeVar('TCase', bound=IVotingCase)


class ChooseBestAnswerPipeline(Generic[TCase]):
    def __init__(self,
                 inner_pipeline: ICasePipeline[TCase],
                 poll_size: int = 3
                 ):
        self.inner_pipeline = inner_pipeline
        self.poll_size = poll_size

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        field_name = Chara.call(CaseRepetition.create_field)('choose_best_answer')
        tracker = CaseRepetition.Tracker(self.inner_pipeline, field_name, CaseCollection(cases.successes))

        for i in range(self.poll_size):
            tracker.iteration([s.case for s in tracker.get_state()])

        result = []
        for summary in tracker.get_state():
            err = summary.create_error_case_if_no_successes(True)
            if err is not None:
                result.append(err)
                continue
            fingerprint_to_candidates = {}
            for case in summary.successes:
                fingerprint = case.get_result_fingerprint()
                if fingerprint not in fingerprint_to_candidates:
                    fingerprint_to_candidates[fingerprint] = []
                fingerprint_to_candidates[fingerprint].append(case)
            best_fingerprint = min(fingerprint_to_candidates, key=lambda fp: (-len(fingerprint_to_candidates[fp]), fp))
            result.append(fingerprint_to_candidates[best_fingerprint][0])

        return CaseCollection(cases.errors, result)
