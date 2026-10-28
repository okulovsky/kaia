from chara.common import CasePrioritization
from ..activity import ImageRequest
from .dto import ImageSetupStatistics


class ImagePrioritization(CasePrioritization[ImageRequest, tuple]):
    """Balances the generated images between the groups of setups that share the same
    stratification key. Reads nothing: the statistics are the ones already collected."""

    def __init__(self,
                 statistics: list[ImageSetupStatistics],
                 stratification_fields: tuple[str, ...],
                 strategy: CasePrioritization.Strategy,
                 budget: int,
                 max_cases_per_fingerprint: int|None = None,
                 ):
        super().__init__(strategy, budget, max_cases_per_fingerprint)
        self.statistics = statistics
        self.stratification_fields = stratification_fields

    def case_to_fingerprint(self, case: ImageRequest) -> tuple:
        return case.setup.to_fingerprint().stratification_key(self.stratification_fields)

    def collect_statistics(self, fingerprints):
        for stat in self.statistics:
            key = stat.setup.to_fingerprint().stratification_key(self.stratification_fields)
            if key in fingerprints:
                fingerprints[key].existing += sum(a.generated for a in stat.activity_status.values())
