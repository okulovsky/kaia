from kaia.brainbox import BrainBoxTestApi, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor
from kaia.brainbox.deciders.utils.fake_dub_decider import FakeDubDecider
from kaia.avatar.server import AvatarTestApi, BrainBoxDubbingService, AvatarSettings
from kaia.avatar.narrator import DummyNarrator
from unittest import TestCase
from uuid import uuid4
from kaia.infra import FileIO
import json

def task_generator(s, voice):
    def _selector(z):
        return z[0]
    task = BrainBoxTask(str(uuid4()), 'fake_tts', dict(text=s, voice=voice))
    return BrainBoxTaskPack(
        task,
        (),
        DownloadingPostprocessor(0, FileIO.read_json)
    )



class AvatarDubbingTestCase(TestCase):
    def test_dubbing(self):
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
            dubbing_service = BrainBoxDubbingService(
                task_generator,
                bb_api
            )
            with AvatarTestApi(AvatarSettings(), DummyNarrator('test_voice'), dubbing_service, None) as avatar_api:
                result = avatar_api.dub_string('Test message')
                self.assertDictEqual(
                    {'voice': 'test_voice', 'text': 'Test message', 'option_index': 0},
                    result.data
                )


