import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Any
from ..cases import TCase, CaseCollection
from ...architecture import Chara, logger
from .selection_table import build_selection_table, format_selection_table

TFingerprint = TypeVar('TFingerprint')


@dataclass
class PrioritizationItem(Generic[TCase, TFingerprint]):
    fingerprint: TFingerprint
    cases: list[TCase] = field(default_factory=list)
    existing: int = 0
    usage: float|None = None


class CasePrioritization(Generic[TCase, TFingerprint], ABC):
    """Selects which cases of the collection are processed in this run, so that the entries
    produced for different fingerprints stay balanced. The selection happens once, from the
    statistics collected before the run; the feedback comes from the next run.

    Selected cases are returned as successes, the others get the NOT_SELECTED error."""

    NOT_SELECTED = 'Not selected by CasePrioritization'

    class Strategy(Enum):
        only_new = 'only_new'
        expand = 'expand'

    def __init__(self,
                 strategy: 'CasePrioritization.Strategy',
                 budget: int,
                 max_cases_per_fingerprint: int|None = None,
                 ):
        self.strategy = strategy
        self.budget = budget
        self.max_cases_per_fingerprint = max_cases_per_fingerprint

    def case_to_fingerprint(self, case: TCase) -> TFingerprint:
        return case.to_fingerprint()

    @abstractmethod
    def collect_statistics(self, fingerprints: dict[TFingerprint, PrioritizationItem[TCase, TFingerprint]]):
        """Fills `existing` and `usage` of the given items in place"""

    def effective_existing(self, existing: int, usage: float|None) -> float:
        """How many fresh entries the existing ones are worth: they are discounted by the
        plays per entry, once each entry was consumed more than once on average"""
        if usage is None or existing == 0:
            return existing
        return existing / max(1.0, usage / existing)

    def _cap(self, item: PrioritizationItem) -> int:
        if self.max_cases_per_fingerprint is None:
            return len(item.cases)
        return min(len(item.cases), self.max_cases_per_fingerprint)

    def _collect_statistics_values(self, items: list[PrioritizationItem]) -> list[tuple[int, float|None]]:
        self.collect_statistics({item.fingerprint: item for item in items})
        return [(item.existing, item.usage) for item in items]

    def _select_only_new(self, items: list[PrioritizationItem]) -> dict[int, list]:
        candidates = []
        for index, item in enumerate(items):
            if item.existing == 0:
                for case in random.sample(item.cases, self._cap(item)):
                    candidates.append((index, case))
        random.shuffle(candidates)
        selected = {index: [] for index in range(len(items))}
        for index, case in candidates[:self.budget]:
            selected[index].append(case)
        return selected

    def _select_expand(self, items: list[PrioritizationItem]) -> dict[int, list]:
        remaining = {index: random.sample(item.cases, len(item.cases)) for index, item in enumerate(items)}
        selected = {index: [] for index in range(len(items))}
        levels = {index: self.effective_existing(item.existing, item.usage) for index, item in enumerate(items)}
        active = [index for index, item in enumerate(items) if self._cap(item) > 0]
        taken = 0
        while taken < self.budget and len(active) > 0:
            lowest = min(levels[index] for index in active)
            index = random.choice([i for i in active if levels[i] == lowest])
            item = items[index]
            selected[index].append(remaining[index].pop())
            taken += 1
            levels[index] = self.effective_existing(item.existing + len(selected[index]), item.usage)
            if len(selected[index]) >= self._cap(item):
                active.remove(index)
        return selected

    def _log(self, items: list[PrioritizationItem], selected: dict[int, list]):
        if self.strategy == CasePrioritization.Strategy.only_new:
            level_name = 'existing'
            level = lambda item, added: item.existing + added
        else:
            level_name = 'effective_existing'
            level = lambda item, added: self.effective_existing(item.existing + added, item.usage)
        table = build_selection_table([
            (level(item, 0), level(item, len(selected[index])), self._cap(item), len(selected[index]))
            for index, item in enumerate(items)
        ])
        total = sum(len(s) for s in selected.values())
        logger.info(
            f'CasePrioritization ({self.strategy.value}, budget {self.budget}): '
            f'{len(items)} fingerprint(s), {total} case(s) selected\n'
            + format_selection_table(level_name, table)
        )

        left_cases = 0
        left_fingerprints = 0
        for index, item in enumerate(items):
            if item.existing != 0:
                continue
            left = self._cap(item) - len(selected[index])
            if left > 0:
                left_cases += left
                left_fingerprints += 1
        if left_cases > 0:
            logger.info(
                f'WARNING: {left_cases} new case(s) in {left_fingerprints} fingerprint(s) '
                f'not processed: budget exhausted'
            )

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        cases = cases.clone()

        by_fingerprint: dict[Any, PrioritizationItem] = {}
        for case in cases.successes:
            fingerprint = self.case_to_fingerprint(case)
            if fingerprint not in by_fingerprint:
                by_fingerprint[fingerprint] = PrioritizationItem(fingerprint)
            by_fingerprint[fingerprint].cases.append(case)
        items = list(by_fingerprint.values())

        # The values are returned rather than read from the items, so that a cached call
        # still fills them
        values = Chara.call(self._collect_statistics_values, 'collect_statistics')(items)
        for item, (existing, usage) in zip(items, values):
            item.existing = existing
            item.usage = usage

        if self.strategy == CasePrioritization.Strategy.only_new:
            selected = self._select_only_new(items)
        elif self.strategy == CasePrioritization.Strategy.expand:
            selected = self._select_expand(items)
        else:
            raise ValueError(f"Unknown strategy {self.strategy}")

        self._log(items, selected)

        selected_ids = set(id(case) for s in selected.values() for case in s)
        for case in cases.successes:
            if id(case) not in selected_ids:
                case.error = CasePrioritization.NOT_SELECTED
        return cases
