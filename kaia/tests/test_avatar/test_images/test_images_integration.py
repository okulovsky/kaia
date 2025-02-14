from brainbox import BrainBoxApi, BrainBoxTask, BrainBoxExtendedTask, DownloadingPostprocessor
from brainbox.deciders import FakeFile, Collector
from kaia.avatar import AvatarApi, AvatarSettings,  AnyContentStrategy, MediaLibraryManager, ImageServiceSettings
from unittest import TestCase
from uuid import uuid4
from kaia.common import Loc
from kaia.dub.languages.en import *
from yo_fluq import Query
import json

def task_generator(s, voice):
    task = BrainBoxTask(decider='fake_image', arguments=dict(text=s, voice=voice))
    return BrainBoxExtendedTask(task, postprocessor=DownloadingPostprocessor(0))


class AvatarDubbingTestCase(TestCase):
    def test_images(self):
        with BrainBoxApi.ServerlessTest([FakeFile(), Collector()]) as bb_api:

            #Creating a media library with pseudo images
            pack = (Query
                    .combinatorics.grid(character=['character_0', 'character_1'], scene=['kitchen', 'forest'])
                    .feed(Collector.FunctionalTaskBuilder(lambda z: BrainBoxTask.call(FakeFile)(z, array_length=10)))
                    )
            media_library_path = bb_api.cache_folder/bb_api.execute(pack)

            #Testing that the images returned are indeed correct
            with Loc.create_test_file() as stats_file:
                image_manager = MediaLibraryManager(AnyContentStrategy(), media_library_path, stats_file)
                image_settings = ImageServiceSettings(image_manager)
                with AvatarApi.Test(AvatarSettings(image_settings=image_settings)) as avatar_api:
                    avatar_api.state_change(dict(character='character_0'))
                    for i in range(10):
                        result = avatar_api.image_get_new()
                        dct = json.loads(result.content)
                        self.assertIn('option_index', dct)
                        self.assertIn('character', dct)
                        self.assertEqual('character_0', dct['character'])
                        result1 = avatar_api.image_get_current()
                        self.assertEqual(result.content, result1.content)

                    avatar_api.state_change(dict(character='character_1'))
                    for i in range(10):
                        result = avatar_api.image_get_new()
                        dct = json.loads(result.content)
                        self.assertIn('option_index', dct)
                        self.assertIn('character', dct)
                        self.assertEqual('character_1', dct['character'])
                        result1 = avatar_api.image_get_current()
                        self.assertEqual(result.content, result1.content)



