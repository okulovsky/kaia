from unittest import TestCase
from kaia.dub import Template
from brainbox import MediaLibrary, BrainBoxApi
from brainbox.deciders import FakeFile
from kaia.common import Loc
from kaia.avatar import (
    AvatarApi, AvatarSettings, TestTaskGenerator, MediaLibraryManager,
    NewContentStrategy, ExactTagMatcher, ParaphraseServiceSettings
)

from kaia.avatar.world import World



class ParaphraseTestCase(TestCase):
    def test_paraphrases(self):
        template_tag = 'template'
        templates = [
            Template("Original text 1").with_name('test_1').paraphrase(),
            Template("Original text 2").with_name('test_2').paraphrase.after()
        ]
        records = [
            MediaLibrary.Record(
                f'{template.name}/{character}/{option}',
                None,
                tags = {
                    template_tag:template.name,
                    World.character.field_name: character,
                    'option': option
                },
                inline_content=f'{template.name}/{character}/{option}'
            )
            for template in templates
            for character in ['character_0', 'character_1']
            for option in range(3)
        ]
        ml = MediaLibrary(tuple(records))

        with BrainBoxApi.Test([FakeFile()]) as bb_api:
            with Loc.create_test_folder() as path:
                ml_path = path/'media_library.zip'
                ml.save(ml_path)
                manager = MediaLibraryManager(
                    NewContentStrategy(False),
                    ml_path,
                    path/'feedback',
                    ExactTagMatcher.SubsetFactory(World.character.field_name)
                )
                settings = AvatarSettings(
                    brain_box_api=bb_api,
                    paraphrase_settings=ParaphraseServiceSettings(manager, template_tag),
                    dubbing_task_generator=TestTaskGenerator()
                )
                with AvatarApi.Test(settings) as api:
                    preview = api.dub(templates[0].utter())
                    self.assertEqual('Test_1/character_0/0.', preview.full_text)

                    preview = api.dub(templates[0]())
                    self.assertEqual('Test_1/character_0/1.', preview.full_text)

                    preview = api.dub(templates[1].utter())
                    self.assertEqual('Original text 2. Test_2/character_0/0.', preview.full_text)

                    api.state_change({World.character.field_name: 'character_1'})
                    preview = api.dub(templates[0].utter())
                    self.assertEqual('Test_1/character_1/0.', preview.full_text)

                    api.state_change({'mood': 'sad'})
                    preview = api.dub(templates[0].utter())
                    self.assertEqual('Test_1/character_1/1.', preview.full_text)

                    api.state_change({World.character.field_name:'character_2'})
                    preview = api.dub(templates[0].utter())
                    self.assertEqual('Original text 1.', preview.full_text)





