from unittest import TestCase

from chara import CaseCollection
from chara.voice_clone.distillation.upsampling import Upsampling, Verifier
from chara.voice_clone.common import ChatterboxModel, ChatterboxInference
from chara.common import Language, Chara
from brainbox import BrainBox, File, ISelfManagingDecider
from brainbox.deciders import Collector
from yo_fluq import FileIO
from foundation_kaia.misc import Loc


class MockVoiceover(ISelfManagingDecider):
    def get_name(self):
        return "Chatterbox"

    def voiceover(self, text: str, speaker: str, language: str = 'en', exaggeration: float = 0.5, cfg_weight: float = 0.5):
        return File(self.current_job_id + '.wav', text.encode('utf-8'))


class MockVosk(ISelfManagingDecider):
    def get_name(self):
        return "Vosk"

    def transcribe_to_array(self, file: str, model: str | None = None):
        text = FileIO.read_text(self.cache_folder / file)
        return [dict(word=w, start=i, end=i + 1) for i, w in enumerate(text.split(' '))]


class StepTestCase(TestCase):
    def test_step(self):
        strings = [
            "The fox chases a rabbit",
            "The rabbit eats a carrot"
        ]
        with BrainBox.Api.test([MockVosk(), MockVoiceover(), Collector()]) as api:
            Chara.Apis.brainbox_api = api
            with Loc.create_test_folder() as folder:
                Chara.start(folder)
                verifier = Verifier(Language.English(), 2, 2, 2)
                pipe = Upsampling.Pipeline(verifier, 'The beginning. ', ' The end.')

                model = ChatterboxModel('test', 'test')
                inference = ChatterboxInference()
                cases = [Upsampling.Case(inference, model, s) for s in strings]
                successes = Chara.call(pipe)(CaseCollection(cases)).raise_if_any_error().successes

                self.assertEqual('fox', successes[0].verification.slice[1]['word'])
                self.assertEqual('rabbit', successes[1].verification.slice[1]['word'])
