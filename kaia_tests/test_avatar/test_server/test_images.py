from kaia.brainbox import BrainBoxTestApi, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor, MediaLibrary
from kaia.brainbox.deciders.fake_image_generator import FakeImageDecider
from kaia.brainbox.deciders.collector import Collector
from kaia.avatar.server import AvatarTestApi, AvatarSettings, SimpleImageService
from kaia.avatar.narrator import DummyNarrator
from unittest import TestCase
from uuid import uuid4
from kaia.infra import FileIO, Loc
from kaia.avatar.narrator import PictureTaskGenerator
from kaia.avatar.dub.languages.en import *
from yo_fluq_ds import Query
import json

def task_generator(s, voice):
    task = BrainBoxTask(str(uuid4()), 'fake_image', dict(text=s, voice=voice))
    return BrainBoxTaskPack(
        task,
        (),
        DownloadingPostprocessor(0)
    )



class AvatarDubbingTestCase(TestCase):
    def test_images(self):
        services = dict(fake_image=FakeImageDecider(), collector=Collector())
        picture_template = Template("{character} {scene}", character = IdentityDub(), scene=IdentityDub())
        task_generator = PictureTaskGenerator(
            picture_template,
            BrainBoxTask.template('fake_image'),
            BrainBoxTask.template('collector')
        )
        tags = Query.combinatorics.grid(character=['Alice','Bob'], scene=['kitchen','forest']).to_list()
        pack = task_generator.generate_task_pack(tags)
        pack.postprocessor.opener = None
        with BrainBoxTestApi(services) as bb_api:
            media_library_path = bb_api.execute(pack)
            with Loc.create_temp_file('avatar_test', 'json') as stats_file:
                image_service = SimpleImageService(media_library_path, stats_file)
                with AvatarTestApi(AvatarSettings(), DummyNarrator(''), None, image_service) as avatar_api:
                    for i in range(10):
                        result = avatar_api.image_get()
                        dct = json.loads(result.data)
                        self.assertIn('prompt', dct)
                        self.assertIn('option_index', dct)


