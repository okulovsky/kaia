import json
import os
import shutil

from chara import CaseCollection
from chara.voice_clone.common import ChatterboxModel, ChatterboxInference, ChatterboxTrain, VoiceTrain, VoiceInference
from chara.common import Samples, Chara
from unittest import TestCase
from brainbox import BrainBox, File, ISelfManagingDecider
from brainbox.deciders import Collector
from uuid import uuid4
from foundation_kaia.misc import Loc
from pathlib import Path


class MyMock(ISelfManagingDecider):
    def __init__(self):
        self.models = set()

    def get_name(self):
        return "Chatterbox"

    def train(self, speaker: str, file):
        pass

    def voiceover(self, **kwargs) -> File:
        return File(
            str(uuid4()),
            json.dumps(kwargs)
        )


class ChatterboxTrainTest(TestCase):
    def test_train(self):
        with BrainBox.Api.serverless_test([MyMock(), Collector()]) as api:
            Chara.Apis.brainbox_api = api

            with Loc.create_test_folder() as folder:
                os.makedirs(folder / 'source/one')
                shutil.copy(Samples.lina / 'lina1.wav', folder / 'source/one')

                os.makedirs(folder / 'source/two')
                shutil.copy(Samples.lina / 'lina2.wav', folder / 'source/two')
                shutil.copy(Samples.lina / 'lina3.wav', folder / 'source/two')

                Chara.start(folder / 'train')
                train_cases = [
                    VoiceTrain.Case(trainer=ChatterboxTrain(), source=path)
                    for path in sorted((folder / 'source').iterdir())
                ]
                train_result = Chara.call(VoiceTrain.pipeline)(CaseCollection(train_cases)).raise_if_any_error().successes

                self.assertEqual(2, len(train_result))
                self.assertEqual(str(folder / 'source/one'), train_result[0].model.model_source)
                self.assertEqual(str(folder / 'source/two'), train_result[1].model.model_source)
                self.assertIsInstance(train_result[0].model, ChatterboxModel)
                self.assertIsInstance(train_result[1].model, ChatterboxModel)

                cloners = [ChatterboxInference('en', 0.6, 0.6), ChatterboxInference('ru', 0.7, 0.7)]
                texts = ['Text 1', 'Text 2']

                Chara.start(folder / 'infer')
                inference_cases = [
                    VoiceInference.Case(inference=cloner, model=case.model, text=text)
                    for cloner in cloners
                    for case in train_result
                    for text in texts
                ]
                inferred = Chara.call(VoiceInference.pipeline)(CaseCollection(inference_cases)).successes
                self.assertEqual(8, len(inferred))
