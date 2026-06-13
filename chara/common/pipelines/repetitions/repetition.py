from ...architecture import Chara
from ..cases import TCase, CaseCollection, ICasePipeline
from dataclasses import dataclass
from typing import Generic, Iterable
from uuid import uuid4
from copy import deepcopy


@dataclass
class CaseRepetitionSummary(Generic[TCase]):
    case: TCase
    successes: list[TCase]
    errors: list[TCase]

    def create_error_case_if_no_successes(self, error_on_empty: bool) -> TCase|None:
        if len(self.successes)>0:
            return None
        if len(self.errors) == 0 and not error_on_empty:
            return None
        case = deepcopy(self.case)
        if self.case.error is not None:
            if case.error:
                return case
        if len(self.errors) == 0:
            case.error = 'No attempts made'
        case.error = '\n\n'.join(e.error for e in self.errors)
        return case


class CaseRepetitionTracker(Generic[TCase]):
    def __init__(self, inner_pipeline: ICasePipeline[TCase], field_name: str, cases:CaseCollection[TCase]):
        self.inner_pipeline = inner_pipeline
        self.field_name = field_name
        self._state = []
        for index, case in enumerate(cases.cases):
            case = deepcopy(case)
            setattr(case, field_name, index)
            self._state.append(CaseRepetitionSummary(case, [], []))

    def get_state(self):
        return self._state

    def iteration(self, cases: Iterable[TCase]):
        @Chara.phase
        def stash_input():
            return list(cases)

        cases: list[TCase] = Chara.previous.result
        @Chara.phase
        def run_inner_pipeline():
            return self.inner_pipeline(CaseCollection(cases))

        result: CaseCollection[TCase] = Chara.previous.result

        @Chara.phase
        def updating_state():
            dropped_ids = set([getattr(c, self.field_name) for c in cases])
            for case in result.cases:
                id = getattr(case, self.field_name)
                dropped_ids.discard(id)
                if case.error:
                    self._state[id].errors.append(case)
                else:
                    self._state[id].successes.append(case)
            for dropped_id in dropped_ids:
                case = deepcopy(self._state[dropped_id].case)
                case.error = "Dropped"
                self._state[dropped_id].errors.append(case)
            return self._state

        self._state = Chara.previous.result




class CaseRepetition:
    Summary = CaseRepetitionSummary
    Tracker = CaseRepetitionTracker

    @staticmethod
    def create_field(prefix: str|None = None):
        if prefix is not None:
            prefix+='_'
        return prefix+str(uuid4()).replace('-','')

