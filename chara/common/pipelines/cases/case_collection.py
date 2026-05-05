from copy import deepcopy
from typing import Generic, Iterable
from .case import TCase

class CaseCollection(Generic[TCase]):
    def __init__(self, *cases: 'Iterable[TCase]|CaseCollection[TCase]'):
        all_cases = []
        for collection in cases:
            if isinstance(collection, CaseCollection):
                collection = collection.cases
            for case in collection:
                all_cases.append(case)
        self._cases = tuple(all_cases)

    @property
    def cases(self) -> tuple[TCase,...]:
        return self._cases

    @property
    def errors(self) -> tuple[TCase,...]:
        return tuple(c for c in self._cases if c.error is not None)

    @property
    def successes(self) -> tuple[TCase,...]:
        return tuple(c for c in self._cases if c.error is None)

    @property
    def successes_collection(self):
        return CaseCollection(self.successes)

    def clone(self) -> 'CaseCollection[TCase]':
        return CaseCollection((deepcopy(c) for c in self._cases))

    def raise_if_any_error(self) -> 'CaseCollection[TCase]':
        errors = self.errors
        if len(errors) > 0:
            raise ValueError(f"At least one case erroneous:\n{errors[0].error}")
        return self

    def raise_if_all_errors(self) -> 'CaseCollection[TCase]':
        errors = self.errors
        successes = self.successes
        if len(successes) == 0 and len(errors) > 0:
            raise ValueError(f"All cases were erroneous, the first error:\n{errors[0].error}")
        return self




