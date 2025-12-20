import json
import os
import shutil

from chara.voice_clone.common import ChatterboxModel, ChatterboxInference, ChatterboxTrain
from chara.common import Samples, CharaApis
from unittest import TestCase
from brainbox import BrainBox, File
from brainbox.deciders import Mock, Collector
from uuid import uuid4
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

class MyMock(Mock):
    def __init__(self):
        super(MyMock, self).__init__("Chatterbox")
        self.models = set()

    def train(self, speaker: str, sample_file):
        pass

    def voiceover(self, **kwargs) -> File:
        return File(
            str(uuid4()),
            json.dumps(kwargs)
        )


class ChatterboxTrainTest(TestCase):
    def test_train(self):
        with BrainBox.Api.Test([MyMock(), Collector()]) as api:
            CharaApis.brainbox_api = api

            with Loc.create_test_folder() as folder:
                #folder = Path(__file__).parent/'cache'; shutil.rmtree(folder, ignore_errors=True)


                os.makedirs(folder/'source/one')
                shutil.copy(Samples.lina/'lina1.wav', folder/'source/one')

                os.makedirs(folder/'source/two')
                shutil.copy(Samples.lina / 'lina2.wav', folder / 'source/two')
                shutil.copy(Samples.lina / 'lina3.wav', folder / 'source/two')

                cache = ChatterboxTrain.Cache(folder/'train')

                ChatterboxTrain.pipeline(
                    cache,
                    [ChatterboxTrain()],
                    (folder/'source').iterdir()
                )

                train_result = cache.read_result()
                self.assertEqual(2, len(train_result))
                self.assertEqual(str(folder/'source/one'), train_result[0].model_source)
                self.assertEqual(str(folder / 'source/two'), train_result[1].model_source)
                self.assertIsInstance(train_result[0], ChatterboxModel)
                self.assertIsInstance(train_result[1], ChatterboxModel)

                cloners = [ChatterboxInference('en', 0.6, 0.6), ChatterboxInference('ru', 0.7, 0.7)]
                texts = ['Text 1', "Text 2"]

                cache = ChatterboxInference.Cache(folder/'inference')

                ChatterboxInference.pipeline(
                    cache,
                    cloners,
                    train_result,
                    texts
                )

                result = cache.read_result()
                self.assertEqual(8, len(result.wavs))

                for wav in result.wavs:
                    self.assertTrue(wav.path.is_file())
                    js = FileIO.read_json(wav.path)
                    for key, value in js.items():
                        k = key if key != 'speaker' else 'model_name'
                        self.assertEqual(value, wav.metadata[k])


