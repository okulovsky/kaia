from chara.common import CasePrioritization
from .stats_builder import ParaphraseFingerprint
from .uterance_paraphrase_case import UtteranceParaphraseCase


class ParaphrasePrioritization(CasePrioritization[UtteranceParaphraseCase, ParaphraseFingerprint]):
    """Reads nothing: the statistics are the ones `build_statistics` put into `case.stats`,
    so that the report and the prioritization see the same numbers"""

    def __init__(self, strategy: CasePrioritization.Strategy, budget: int):
        super().__init__(strategy, budget)

    def collect_statistics(self, fingerprints):
        for item in fingerprints.values():
            stats = item.cases[0].stats
            item.existing = stats.existing
            item.usage = float(stats.seen)
