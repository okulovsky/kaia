import json
from pathlib import Path
from unittest import TestCase

from avatar.app import AvatarApi
from avatar.daemon import ImageService
from avatar.daemon.image_service.media_library import MediaLibrary
from foundation_kaia.marshalling import Serializer
from foundation_kaia.misc import Loc

from chara import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.images.common import Theme
from chara.images.common.generation import PackagePipeline, MediaLibraryDescriptionItem
from chara.images.common.drawing import DrawingCase, VariantCase
from chara.images.krea import KreaCase, KreaSettings, KreaImageToImage

_DESCRIPTION_SERIALIZER = Serializer.parse(list[MediaLibraryDescriptionItem])
_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'


class PackagePipelineTestCase(TestCase):
    def test_packages_main_image_variants_and_description(self):
        character = Character(name='Miku', gender=Character.Gender.Feminine, description='desc')
        theme = Theme(location='forest', season='summer')
        settings = KreaSettings(workflow_template=KreaImageToImage('', '', width=1024, height=1024))
        scenario = KreaCase(character=character, settings=settings, theme=theme, activity='cooking')

        with Loc.create_test_folder() as image_folder:
            main_image = image_folder / 'main.png'
            main_image.write_bytes(_PNG_BYTES)
            variant_image = image_folder / 'variant.png'
            variant_image.write_bytes(_PNG_BYTES)

            case = DrawingCase(
                scenario=scenario,
                workflow=scenario.to_workflow(),
                image=main_image,
                variants={'variant_0': VariantCase(prompt='a variant prompt', image=variant_image)},
            )

            with Loc.create_test_folder() as avatar_folder:
                with AvatarApi.test(avatar_folder) as avatar_api:
                    Chara.Apis.avatar_api = avatar_api

                    with Loc.create_test_folder() as work_folder:
                        Chara.start(work_folder)
                        pipeline = PackagePipeline()
                        Chara.call(pipeline)(CaseCollection([case]))

                    resources = avatar_api.resources(ImageService)
                    files = resources.list('/')
                    zip_files = [f for f in files if f.endswith('.zip')]
                    self.assertEqual(1, len(zip_files))
                    media_zip = zip_files[0]

                    description_files = [f for f in files if f.endswith(ImageService.DESCRIPTION_SUFFIX)]
                    self.assertEqual([f'{media_zip}{ImageService.DESCRIPTION_SUFFIX}'], description_files)

                    with Loc.create_test_folder() as download_folder:
                        local_zip = resources.download(media_zip, download_folder)
                        media_library = MediaLibrary(local_zip)

                    self.assertEqual(2, len(media_library.records))
                    main_record = next(r for r in media_library.records if 'variant_type' not in r.tags)
                    variant_record = next(r for r in media_library.records if 'variant_type' in r.tags)

                    self.assertEqual(
                        dict(character='Miku', activity='cooking', location='forest', season='summer'),
                        main_record.tags,
                    )
                    self.assertEqual(
                        dict(original=main_record.path, variant_type='variant_0'),
                        variant_record.tags,
                    )

                    desc_bytes = resources.read(description_files[0])
                    descriptions = _DESCRIPTION_SERIALIZER.from_json(json.loads(desc_bytes))
                    self.assertEqual(1, len(descriptions))
                    self.assertEqual(main_record.path, descriptions[0].file_id)
                    self.assertEqual('cooking', descriptions[0].image_fingerprint.activity)
                    self.assertEqual('Miku', descriptions[0].image_fingerprint.setup_fingerprint.character_name)
