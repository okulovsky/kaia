from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, CaseCollection, CasePrioritization
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, ImageSetup, ActivityCase, ActivityCatalogItem, ActivityPrioritization


def _case(name: str) -> ActivityCase:
    return ActivityCase(ImageSetup(Character(name=name, gender=Character.Gender.Feminine, description='desc'), Theme(location='forest')))


def _catalog(counts: dict[str, int]):
    catalog = {}
    for name, count in counts.items():
        fingerprint = _case(name).to_fingerprint()
        catalog[fingerprint] = ActivityCatalogItem(fingerprint, [f'{name}{i}' for i in range(count)])
    return catalog


def _select(catalog, strategy, budget) -> list[str]:
    cases = CaseCollection([_case(name) for name in ('A', 'B', 'C')])
    with Loc.create_test_folder() as folder:
        Chara.start(folder)
        result = ActivityPrioritization(catalog, strategy, budget)(cases)
    return sorted(c.character.name for c in result.successes)


class ActivityPrioritizationTestCase(TestCase):
    def test_only_new_skips_setups_with_activities(self):
        catalog = _catalog({'A': 3})
        self.assertEqual(['B', 'C'], _select(catalog, CasePrioritization.Strategy.only_new, 10))

    def test_expand_prefers_fewest_activities(self):
        catalog = _catalog({'A': 3, 'B': 1, 'C': 5})
        self.assertEqual(['A', 'B'], _select(catalog, CasePrioritization.Strategy.expand, 2))
