import json
from pathlib import Path
from unittest import TestCase

from avatar.app import AvatarApi
from avatar.daemon import ImageService
from foundation_kaia.marshalling import Serializer
from foundation_kaia.misc import Loc

from chara import Chara
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, ImageSetup
from chara.images.common.activity.fingerprint import ImageFingerprint
from chara.images.common.generation import ImageStatisticsPipeline, MediaLibraryDescriptionItem
from chara.images.common.drawing import DrawingCase
from chara.images.krea import KreaCase, KreaSettings, KreaImageToImage

_DESCRIPTION_SERIALIZER = Serializer.parse(list[MediaLibraryDescriptionItem])


def _character(name: str) -> Character:
    return Character(name=name, gender=Character.Gender.Feminine, description='desc')


def _drawing_case(character: Character, theme: Theme, activity: str) -> DrawingCase:
    settings = KreaSettings(workflow_template=KreaImageToImage('', '', width=1024, height=1024))
    scenario = KreaCase(character=character, settings=settings, theme=theme, activity=activity)
    return DrawingCase(scenario=scenario, workflow=scenario.to_workflow(), image=Path('/tmp/fake.png'))


def _upload_descriptions(avatar_api: AvatarApi, filename: str, descriptions: list[MediaLibraryDescriptionItem]) -> None:
    data = json.dumps(_DESCRIPTION_SERIALIZER.to_json(descriptions)).encode('utf-8')
    avatar_api.resources(ImageService).upload(f'{filename}{ImageService.DESCRIPTION_SUFFIX}', data)


class ImageStatisticsPipelineTestCase(TestCase):
    def test_combines_catalog_descriptions_and_feedback(self):
        miku = _character('Miku')
        theme = Theme(location='forest', season='summer')
        setup = ImageSetup(miku, theme)
        fingerprint = setup.to_fingerprint()

        rin_setup = ImageSetup(_character('Rin'), Theme(location='city'))
        rin_fingerprint = rin_setup.to_fingerprint()

        with Loc.create_test_folder() as avatar_folder:
            with AvatarApi.test(avatar_folder) as avatar_api:
                Chara.Apis.avatar_api = avatar_api

                descriptions = [
                    MediaLibraryDescriptionItem(
                        file_id='miku_cooking_1.png',
                        image_fingerprint=ImageFingerprint(fingerprint, 'cooking'),
                        case=_drawing_case(miku, theme, 'cooking'),
                    ),
                    MediaLibraryDescriptionItem(
                        file_id='miku_cooking_2.png',
                        image_fingerprint=ImageFingerprint(fingerprint, 'cooking'),
                        case=_drawing_case(miku, theme, 'cooking'),
                    ),
                    # Belongs to a setup that isn't part of this run - must be dropped.
                    MediaLibraryDescriptionItem(
                        file_id='rin_dancing_1.png',
                        image_fingerprint=ImageFingerprint(rin_fingerprint, 'dancing'),
                        case=_drawing_case(_character('Rin'), Theme(location='city'), 'dancing'),
                    ),
                ]
                _upload_descriptions(avatar_api, 'media_library-0000.zip', descriptions)

                feedback = {
                    'miku_cooking_1.png': {'seen': 3, 'good': 2},
                    'miku_cooking_2.png': {'seen': 1, 'bad': 1},
                    # No matching description - must be skipped, not crash.
                    'unknown_file.png': {'seen': 5},
                }
                avatar_api.resources(ImageService).upload(
                    'images-feedback.json', json.dumps(feedback).encode('utf-8')
                )

                with Loc.create_test_folder() as work_folder:
                    Chara.start(work_folder)
                    catalog_path = work_folder / 'catalog.yaml'
                    from chara.images.common.activity.activity_catalog_item import ActivityCatalogItem
                    ActivityCatalogItem.write_catalog(
                        catalog_path,
                        {fingerprint: ActivityCatalogItem(fingerprint, ['cooking', 'reading'])},
                    )

                    pipeline = ImageStatisticsPipeline(catalog_path)
                    result = Chara.call(pipeline)([setup])

        self.assertEqual(1, len(result))
        setup_stats = result[0]
        self.assertIs(setup, setup_stats.setup)

        cooking = setup_stats.activity_status['cooking']
        self.assertEqual(2, cooking.generated)
        self.assertEqual(4, cooking.seen)
        self.assertEqual(2, cooking.good)
        self.assertEqual(1, cooking.bad)

        reading = setup_stats.activity_status['reading']
        self.assertEqual(0, reading.generated)
        self.assertEqual(0, reading.seen)
        self.assertEqual(0, reading.good)
        self.assertEqual(0, reading.bad)

    def test_setup_with_no_catalog_entry_has_no_activities(self):
        setup = ImageSetup(_character('Nobody'), Theme(location='void'))

        with Loc.create_test_folder() as avatar_folder:
            with AvatarApi.test(avatar_folder) as avatar_api:
                Chara.Apis.avatar_api = avatar_api

                with Loc.create_test_folder() as work_folder:
                    Chara.start(work_folder)
                    pipeline = ImageStatisticsPipeline(work_folder / 'nonexistent_catalog.yaml')
                    result = Chara.call(pipeline)([setup])

        self.assertEqual(1, len(result))
        self.assertEqual({}, result[0].activity_status)
