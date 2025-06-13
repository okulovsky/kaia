from brainbox import BrainBoxApi
from brainbox.deciders import FakeFile
from avatar import AvatarApi, AvatarSettings, TestTaskGenerator, WorldFields
from unittest import TestCase
import json


class AvatarDubbingTestCase(TestCase):
    def test_dubbing(self):
        with BrainBoxApi.Test([FakeFile()]) as bb_api:
            with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api, dubbing_task_generator=TestTaskGenerator())) as avatar_api:
                preview = avatar_api.dub('Test one. Test two')
                self.assertEqual(2, len(preview.jobs))
                result = avatar_api.dub_get_result(preview.jobs[0])
                self.assertDictEqual(
                    {'voice': 'voice_0', 'text': 'Test one.'},
                    json.loads(result.content)
                )
                result = avatar_api.dub_get_result(preview.jobs[1])
                self.assertDictEqual(
                    {'voice': 'voice_0', 'text': 'Test two.'},
                    json.loads(result.content)
                )
                avatar_api.state_change({WorldFields.character:'character_1'})
                preview = avatar_api.dub('Test three.')
                self.assertEqual(1, len(preview.jobs))
                result = avatar_api.dub_get_result(preview.jobs[0])
                self.assertDictEqual(
                    {'voice': 'voice_1', 'text': 'Test three.'},
                    json.loads(result.content)
                )





