from chara.common import CasePrioritization
from .case import ActivityCase
from .fingerprint import ImageSetupFingerprint
from .activity_catalog_item import ActivityCatalogItem


class ActivityPrioritization(CasePrioritization[ActivityCase, ImageSetupFingerprint]):
    """Prioritizes the setups with the fewest activities in the catalog"""

    def __init__(self,
                 catalog: dict[ImageSetupFingerprint, ActivityCatalogItem],
                 strategy: CasePrioritization.Strategy,
                 budget: int,
                 ):
        super().__init__(strategy, budget)
        self.catalog = catalog

    def collect_statistics(self, fingerprints):
        for fingerprint, item in fingerprints.items():
            catalog_item = self.catalog.get(fingerprint)
            item.existing = 0 if catalog_item is None else len(catalog_item.activities)
