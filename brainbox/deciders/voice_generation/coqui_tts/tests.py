from .api import CoquiTTS
from ....framework import TestReport, BrainBox, File
from ...common import VOICEOVER_TEXT, check_if_its_sound
from unittest import TestCase
from pathlib import Path
from .settings import CoquiTTSSettings

TEST_VOICE_PATH = Path(__file__).parent / 'test_voice.wav'


class Test:
    def __init__(self, api: BrainBox.Api, tc: TestCase):
        self.api = api
        self.tc = tc

    def test_dub(self):
        file = self.api.open_file(self.api.execute(
            BrainBox.Task.call(CoquiTTS).dub(text=VOICEOVER_TEXT)
        ))
        yield TestReport.last_call(self.api).result_is_file(File.Kind.Audio).with_comment("Voiceover")
        check_if_its_sound(file.content, self.tc)



    def test_voice_clone(self):
        file = self.api.open_file(self.api.execute(
            BrainBox.Task.call(CoquiTTS).voice_clone(VOICEOVER_TEXT, voice='test_voice')
        ))
        yield (
            TestReport
            .last_call(self.api)
            .result_is_file(File.Kind.Audio)
            .with_uploaded_file('test_voice', File.read(TEST_VOICE_PATH))
            .with_comment("Voice clone")
        )
        check_if_its_sound(file.content, self.tc)

    def load_model_and_repr_description(self, model_name: str):
        yield TestReport.section(f"Model {model_name}")
        self.api.execute(BrainBox.Task.call(CoquiTTS).load_model(model_name))
        yield TestReport.last_call(self.api).with_comment("Loading model (will be used if no `model` provided in decider's call)")




    def test_all(self, settings: CoquiTTSSettings):
        CoquiTTS.upload_voice(TEST_VOICE_PATH).execute(self.api)

        for model in settings.builtin_models_to_download:
            yield from self.load_model_and_repr_description(model.model_name)
            if model.test_dub:
                yield from self.test_dub()
            if model.test_voice_clone:
                yield from self.test_voice_clone()

        custom_models_files = self.api.controller_api.list_resources(CoquiTTS, 'custom')
        if custom_models_files is None:
            return
        print(custom_models_files)
        custom_models = [
            c.split('/')[-1]
            for c in custom_models_files
            if c.endswith('.pth') and not c.endswith('.speakers.pth')
        ]

        for custom_model in custom_models:
            yield from self.load_model_and_repr_description('custom/'+custom_model)
            yield from self.test_dub()





