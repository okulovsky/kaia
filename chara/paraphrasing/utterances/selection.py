import random
from abc import ABC, abstractmethod
from typing import Iterable

from chara.common import CaseRepetition, logger
from .stats_builder import ParaphraseFingerprint, ParaphraseStats
from .uterance_paraphrase_case import UtteranceParaphraseCase

Summary = CaseRepetition.Summary[UtteranceParaphraseCase]
LOGGED_ROWS = 10


class ICaseSelection(ABC):
    """What a run generates, and when it ends.

    `BatchingPipeline` asks for a batch, runs it, and asks again; returning an empty
    list ends the run. So the whole policy of a run lives here, and the pipeline has
    no settings of its own.

    A case is never repeated inside one batch. Whether it may come back in a later
    batch is up to the selection: `NewEntitiesSelection` says no, one round covers it,
    while `DeficitSelection` says yes, that is how the worn ones get topped up.

    `max_errors` gives up on a case that keeps failing: once it has failed that many
    times, it is not passed to a batch again for the rest of the run.
    """

    def __init__(self, max_errors: int):
        self.max_errors = max_errors
        self.processed: dict[ParaphraseFingerprint, int] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Names the run folder, so one behaviour never resumes another's run."""

    def gave_up(self, summary: Summary) -> bool:
        return len(summary.errors) >= self.max_errors

    def _hand_out(self, summaries: list[Summary]) -> list[UtteranceParaphraseCase]:
        """Records what is going out, so the report can show how often a case was tried."""
        cases = []
        for summary in summaries:
            fingerprint = summary.case.stats.fingerprint
            self.processed[fingerprint] = self.processed.get(fingerprint, 0) + 1
            cases.append(summary.case)
        return cases

    @abstractmethod
    def report_plan(self, stats: Iterable[ParaphraseStats]) -> None:
        """Logs the pool this selection sees and what it intends to do, before any task is sent."""

    @abstractmethod
    def __call__(self, summaries: list[Summary]) -> list[UtteranceParaphraseCase]:
        pass


class NewEntitiesSelection(ICaseSelection):
    """Cases with no paraphrases at all: a newly added template, character or user.

    One round of paraphrasing covers a case, so a case that produced something is not
    offered again; one that failed is retried until it has failed `max_errors` times.
    There is nothing to rank -- every candidate is equally uncovered -- so they go in
    the order the manager produced them, which is stable across runs. The run ends when
    every uncovered case has had its turn.
    """

    name = 'new_entities'

    def __init__(self,
                 batch_size: int = 30,
                 budget: int|None = None,
                 max_errors: int = 3,
                 ):
        super().__init__(max_errors)
        self.batch_size = batch_size
        self.budget = budget
        self.spent = 0

    def report_plan(self, stats: Iterable[ParaphraseStats]) -> None:
        uncovered = [s for s in stats if s.existing == 0]
        budget = 'no budget' if self.budget is None else f'budget {self.budget} case(s)'
        logger.info(
            f"{type(self).__name__}: {len(uncovered)} case(s) with no paraphrases, "
            f"in batches of {self.batch_size}, {budget}"
        )

    def __call__(self, summaries: list[Summary]) -> list[UtteranceParaphraseCase]:
        batch_size = self.batch_size
        if self.budget is not None:
            batch_size = min(batch_size, self.budget - self.spent)
        if batch_size <= 0:
            return []

        candidates = [
            s for s in summaries
            if s.case.stats is not None
            and s.case.stats.existing == 0
            and len(s.successes) == 0
            and not self.gave_up(s)
        ]
        selection = self._hand_out(candidates[:batch_size])
        self.spent += len(selection)
        return selection


class DeficitSelection(ICaseSelection):
    """Supports what is already there, worst-worn first, until the budget is spent.

    The measure is relative, not absolute: `plays per paraphrase`, how often each
    paraphrase of a case has been heard on average. A case heard 20 times with 5
    paraphrases is at 4.0 and feels far more repetitive than one heard 198 times with
    110, which is at 1.8, even though the second has served more repeats in total.

    Nothing is filtered out. Every case is a candidate, so a batch is always full and
    a budget of 100 cases means paraphrases for 100 cases -- cases that are not worn
    yet simply come last. The run is therefore exactly `budget / batch_size` batches.

    Paraphrases this run produced count towards the pool, so a case that has just been
    served slides down the ranking and lets others up. Ties are broken at random, so the
    flat tail is not the same cases every run.
    """

    name = 'deficit'

    def __init__(self,
                 budget: int = 500,
                 batch_size: int = 50,
                 max_errors: int = 3,
                 ):
        super().__init__(max_errors)
        self.budget = budget
        self.batch_size = batch_size
        self.spent = 0

    @staticmethod
    def plays_per_paraphrase(stats: ParaphraseStats, produced: int = 0) -> float:
        """The relative deficit. Above 1.0 means the user has started hearing repeats."""
        return stats.seen / max(1, stats.existing + produced)

    def _rank(self, summary: Summary) -> float:
        return self.plays_per_paraphrase(summary.case.stats, len(summary.successes))

    def report_plan(self, stats: Iterable[ParaphraseStats]) -> None:
        stats = sorted(stats, key=self.plays_per_paraphrase, reverse=True)
        worn = [s for s in stats if self.plays_per_paraphrase(s) > 1]
        batches = -(-self.budget // self.batch_size)
        logger.info(
            f"{type(self).__name__}: budget {self.budget} case(s) "
            f"in {batches} batch(es) of {self.batch_size}; "
            f"{len(worn)} case(s) already hearing repeats"
        )
        for s in stats[:LOGGED_ROWS]:
            logger.info(
                f"  {s.fingerprint.template_name} "
                f"[{s.fingerprint.language}"
                f"{'' if s.fingerprint.character is None else '/' + s.fingerprint.character}"
                f"{'' if s.fingerprint.record is None else '/' + s.fingerprint.record}] "
                f"seen {s.seen} against {s.existing}, "
                f"{self.plays_per_paraphrase(s):.2f} play(s) per paraphrase"
            )

    def __call__(self, summaries: list[Summary]) -> list[UtteranceParaphraseCase]:
        batch_size = min(self.batch_size, self.budget - self.spent)
        if batch_size <= 0:
            return []

        candidates = [
            s for s in summaries
            if s.case.stats is not None
            and not self.gave_up(s)
        ]
        candidates.sort(key=lambda s: (-self._rank(s), random.random()))
        selection = self._hand_out(candidates[:batch_size])
        self.spent += len(selection)
        return selection
