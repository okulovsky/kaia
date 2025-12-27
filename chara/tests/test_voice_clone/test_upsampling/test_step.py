import time
from unittest import TestCase
from chara.voice_clone.upsampling import StepCache, StepPipeline, Verifier
from chara.voice_clone.common import ChatterboxModel, ChatterboxInference
from chara.common import Language, CharaApis
from brainbox import BrainBox, File
from brainbox.deciders import Mock, Collector
from yo_fluq import FileIO
from foundation_kaia.misc import Loc
from pprint import pprint


class MockVoiceover(Mock):
    def __init__(self):
        super().__init__('Chatterbox')

    def voiceover(self, text: str, speaker: str, language: str = 'en', exaggeration: float = 0.5, cfg_weight: float = 0.5):
        return File(self.current_job_id+'.wav', text.encode('utf-8'))

class MockVosk(Mock):
    def __init__(self):
        super().__init__('Vosk')

    def transcribe_to_array(self, file: str, model_name: str|None = None):
        text = FileIO.read_text(self.cache_folder/file)
        return [dict(word=w, start=i, end=i+1) for i, w in enumerate(text.split(' '))]


class StepTestCase(TestCase):
    def test_step(self):
        strings = [
            "The fox chases a rabbit",
            "The rabbit eats a carrot"
        ]
        with BrainBox.Api.Test([MockVosk(), MockVoiceover(), Collector()]) as api:
            CharaApis.brainbox_api = api
            with Loc.create_test_folder() as folder:
                cache = StepCache(folder)
                verifier = Verifier(Language.English(), 2, 2, 2)
                pipe = StepPipeline('en', verifier, 'The beginning. ', " The end.")

                model = ChatterboxModel('test', 'test')
                inference = ChatterboxInference()
                pipe(cache, inference, model, strings)

                result = cache.read_result()
                self.assertEqual('fox', result[0].verification.slice[1]['word'])
                self.assertEqual('rabbit', result[1].verification.slice[1]['word'])

