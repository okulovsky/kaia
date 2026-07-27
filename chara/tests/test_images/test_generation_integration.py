from collections import Counter
from pathlib import Path
from unittest import TestCase
from uuid import uuid4

from avatar.app import AvatarApi
from avatar.daemon import ImageService
from avatar.daemon.image_service.media_library import MediaLibrary
from foundation_kaia.misc import Loc

from chara import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, ImageSetup, ImageRequest
from chara.images.common.activity.activity_catalog_item import ActivityCatalogItem
from chara.images.common.generation import GenerationPipeline
from chara.images.common.scenario import ScenarioPipeline
from chara.images.common.drawing import DrawingCase
from chara.images.krea import KreaCase, KreaSettings, KreaImageToImage

BUDGET = 4
_SETTINGS = KreaSettings(workflow_template=KreaImageToImage('', '', width=1024, height=1024))
_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'


def _character(name: str) -> Character:
    return Character(name=name, gender=Character.Gender.Feminine, description='desc')


THEME = Theme(location='forest')
SETUPS = {name: ImageSetup(_character(name), THEME) for name in 'ABCDEF'}
SETUPS_LIST = [SETUPS[name] for name in 'ABCDEF']


def _case_factory(request: ImageRequest) -> KreaCase:
    return KreaCase(request.setup.character, _SETTINGS, request.setup.theme, request.activity)


class _FakeDrawingPipeline:
    """Stands in for DrawingPipeline: no BrainBox involved, just materializes
    a real (1x1) PNG per case so the rest of the pipeline (packaging and the
    report images, in particular) has something real to work with."""

    def __init__(self, folder: Path):
        self.folder = folder

    def __call__(self, cases: CaseCollection) -> CaseCollection[DrawingCase]:
        result = []
        for case in cases.cases:
            path = self.folder / f'{uuid4()}.png'
            path.write_bytes(_PNG_BYTES)
            result.append(DrawingCase(scenario=case, image=path))
        return CaseCollection(result)


class GenerationIntegrationTestCase(TestCase):
    def _run_two_generations(self, catalog: dict) -> MediaLibrary:
        """Seeds the activity catalog, then runs the generation pipeline (statistics ->
        balancing -> scenarios -> drawing -> packaging) twice against a real (test)
        avatar server, so the second run's statistics reflect what the first run
        actually uploaded. Returns the resulting MediaLibrary (merged across both runs'
        uploads) for the caller to inspect."""

        with Loc.create_test_folder() as catalog_folder:
            catalog_path = catalog_folder / 'activities.yaml'
            ActivityCatalogItem.write_catalog(catalog_path, catalog)

            with Loc.create_test_folder() as avatar_folder:
                with AvatarApi.test(avatar_folder) as avatar_api:
                    Chara.Apis.avatar_api = avatar_api

                    for _ in range(2):
                        with Loc.create_test_folder() as image_folder:
                            with Loc.create_test_folder() as run_folder:
                                generation_pipeline = GenerationPipeline(
                                    catalog_path,
                                    BUDGET,
                                    ScenarioPipeline(_case_factory, []),
                                    _FakeDrawingPipeline(image_folder),
                                )

                                Chara.start(run_folder)
                                Chara.call(generation_pipeline)(SETUPS_LIST)

                return MediaLibrary.from_folder(
                    avatar_folder / 'resources' / 'ImageService',
                    ImageService.MEDIA_LIBRARY_PREFIX,
                    ImageService.MEDIA_LIBRARY_SUFFIX,
                )

    def test_skewed_catalog_concentrates_on_the_richest_setup(self):
        catalog = {
            SETUPS['A'].to_fingerprint(): ActivityCatalogItem(SETUPS['A'].to_fingerprint(), ['a1', 'a2']),
            SETUPS['B'].to_fingerprint(): ActivityCatalogItem(SETUPS['B'].to_fingerprint(), ['b1', 'b2']),
            SETUPS['C'].to_fingerprint(): ActivityCatalogItem(SETUPS['C'].to_fingerprint(), ['c1', 'c2', 'c3', 'c4']),
            # D, E, F intentionally have no catalog entries at all - zero activities available.
        }

        media_library = self._run_two_generations(catalog)

        counts = Counter(r.tags['character'] for r in media_library.records)
        self.assertEqual(8, len(media_library.records))
        self.assertEqual(Counter({'A': 2, 'B': 2, 'C': 4}), counts)

    def test_uniform_catalog_spreads_budget_evenly(self):
        catalog = {
            SETUPS[name].to_fingerprint(): ActivityCatalogItem(SETUPS[name].to_fingerprint(), [f'{name.lower()}1', f'{name.lower()}2'])
            for name in 'ABCDEF'
        }

        media_library = self._run_two_generations(catalog)

        counts = Counter(r.tags['character'] for r in media_library.records)
        self.assertEqual(8, len(media_library.records))
        # Every setup has the same capacity (2 activities), so which two end up with an
        # extra pick is down to the balancing's randomized tie-breaking - only the shape
        # of the distribution (two setups get 2, the rest get 1) is guaranteed.
        self.assertEqual(set('ABCDEF'), set(counts))
        self.assertEqual([1, 1, 1, 1, 2, 2], sorted(counts.values()))
