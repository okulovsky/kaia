from kaia.brainbox import BrainBoxTestApi
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from kaia.avatar import AvatarTestApi, DubbingService, AvatarSettings, TestTaskGenerator
from kaia.narrator import SimpleNarrator, World
from unittest import TestCase


class AvatarDubbingTestCase(TestCase):
    def test_dubbing(self):
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
            with AvatarTestApi(AvatarSettings(brain_box_api=bb_api, dubbing_task_generator=TestTaskGenerator())) as avatar_api:
                preview = avatar_api.dub('Test one. Test two')
                self.assertEqual(2, len(preview.jobs))
                result = avatar_api.dub_get_result(preview.jobs[0])
                self.assertDictEqual(
                    {'voice': 'voice_0', 'text': 'Test one.', 'option_index': 0},
                    result.data
                )
                result = avatar_api.dub_get_result(preview.jobs[1])
                self.assertDictEqual(
                    {'voice': 'voice_0', 'text': 'Test two.', 'option_index': 0},
                    result.data
                )
                avatar_api.state_change({World.character.field_name:'character_1'})
                preview = avatar_api.dub('Test three.')
                self.assertEqual(1, len(preview.jobs))
                result = avatar_api.dub_get_result(preview.jobs[0])
                self.assertDictEqual(
                    {'voice': 'voice_1', 'text': 'Test three.', 'option_index': 0},
                    result.data
                )





