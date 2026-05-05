from .case import TCase
from dataclasses import dataclass
from typing import Generic, Iterable
from uuid import uuid4
from copy import deepcopy
from .case_collection import CaseCollection

@dataclass
class CaseRepetitionSummary(Generic[TCase]):
    case: TCase
    successes: tuple[TCase,...]
    errors: tuple[TCase,...]

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





class CaseRepetition:
    Summary = CaseRepetitionSummary

    @staticmethod
    def create_field(prefix: str|None = None):
        if prefix is not None:
            prefix+='_'
        return prefix+str(uuid4()).replace('-','')


    @staticmethod
    def prepare(case_id_field: str, cases:CaseCollection[TCase]) -> CaseCollection[TCase]:
        result = []
        for index, case in enumerate(cases.cases):
            case = deepcopy(case)
            setattr(case, case_id_field, index)
            result.append(case)
        return CaseCollection(result)

    @staticmethod
    def parse(case_id_field: str, cases: CaseCollection[TCase], results: Iterable[CaseCollection[TCase]]) -> 'list[CaseRepetitionSummary[TCase]]':
        summaries = [CaseRepetitionSummary[TCase](case, [], []) for case in cases.cases]
        for attempt in results:
            for case in attempt.cases:
                id = getattr(case, case_id_field)
                summary = summaries[id]
                if case.error:
                    summary.errors.append(case)
                else:
                    summary.successes.append(case)
        return summaries