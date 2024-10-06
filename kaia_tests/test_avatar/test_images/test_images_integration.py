from kaia.brainbox import BrainBoxTestApi, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor
from kaia.brainbox.deciders.fake_image_generator import FakeImageDecider
from kaia.brainbox.deciders.collector import Collector
from kaia.avatar import AvatarApi, AvatarSettings,  AnyContentStrategy, MediaLibraryManager
from kaia.narrator.task_generators.images import PictureTaskGenerator
from unittest import TestCase
from uuid import uuid4
from kaia.infra import Loc
from kaia.dub.languages.en import *
from yo_fluq_ds import Query
import json

def task_generator(s, voice):
    task = BrainBoxTask(decider='fake_image', arguments=dict(text=s, voice=voice))
    return BrainBoxTaskPack(
        task,
        (),
        DownloadingPostprocessor(0)
    )



class AvatarDubbingTestCase(TestCase):
    def test_images(self):
        services = dict(fake_image=FakeImageDecider(), Collector=Collector())
        picture_template = Template("{character} {scene}", character = ToStrDub(), scene=ToStrDub())
        task_generator = PictureTaskGenerator(
            picture_template,
            'fake_image',
        )
        tags = Query.combinatorics.grid(character=['character_0','character_1'], scene=['kitchen','forest']).to_list()
        pack = task_generator.generate_task_pack(tags)
        pack.postprocessor.opener = None
        with BrainBoxTestApi(services) as bb_api:
            media_library_path = bb_api.execute(pack)
            with Loc.create_temp_file('avatar_test', 'json') as stats_file:
                image_manager = MediaLibraryManager(AnyContentStrategy(), media_library_path, stats_file)
                with AvatarApi.Test(AvatarSettings(image_media_library_manager=image_manager)) as avatar_api:
                    avatar_api.state_change(dict(character='character_0'))
                    for i in range(10):
                        result = avatar_api.image_get()
                        dct = json.loads(result.data)
                        self.assertIn('prompt', dct)
                        self.assertIn('option_index', dct)
                        self.assertIn('character_0', dct['prompt'])

                    avatar_api.state_change(dict(character='character_1'))
                    for i in range(10):
                        result = avatar_api.image_get()
                        dct = json.loads(result.data)
                        self.assertIn('prompt', dct)
                        self.assertIn('option_index', dct)
                        self.assertIn('character_1', dct['prompt'])


