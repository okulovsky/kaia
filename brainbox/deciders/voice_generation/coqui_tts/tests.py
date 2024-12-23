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
        yield TestReport.H3("Voiceover")
        yield TestReport.text("Input")
        yield TestReport.code(VOICEOVER_TEXT)
        yield TestReport.text("Result")
        file = self.api.download(self.api.execute(
            BrainBox.Task.call(CoquiTTS).dub(text=VOICEOVER_TEXT)
        ))
        check_if_its_sound(file.content, self.tc)
        yield TestReport.file(file)


    def test_voice_clone(self):
        yield TestReport.H3("Voice clone")
        yield TestReport.text("Input")
        yield TestReport.code(VOICEOVER_TEXT)
        yield TestReport.text("Source voice")
        yield TestReport.file(File.read(TEST_VOICE_PATH))
        file = self.api.download(self.api.execute(
            BrainBox.Task.call(CoquiTTS).voice_clone(VOICEOVER_TEXT, voice='test_voice')
        ))
        check_if_its_sound(file.content, self.tc)
        yield TestReport.text("Result")
        yield TestReport.file(file)

    def load_model_and_repr_description(self, model_name: str):
        yield TestReport.H2(f"Model {model_name}")
        model_description = self.api.execute(BrainBox.Task.call(CoquiTTS).load_model(model_name))
        if model_description['speakers'] is not None and len(model_description['speakers']) > 5:
            model_description['speakers'] = model_description['speakers'][:5] + ['...']
        yield TestReport.json(model_description)


    def test_all(self, settings: CoquiTTSSettings):
        CoquiTTS.upload_voice(self.api, TEST_VOICE_PATH)
        yield TestReport.H1("Built-in models")
        for model in settings.builtin_models_to_download:
            yield from self.load_model_and_repr_description(model.model_name)
            if model.test_dub:
                yield from self.test_dub()
            if model.test_voice_clone:
                yield from self.test_voice_clone()

        custom_models_files = self.api.controller_api.list_resources(CoquiTTS, 'custom')
        print(custom_models_files)
        custom_models = [
            c.split('/')[-1]
            for c in custom_models_files
            if c.endswith('.pth') and not c.endswith('.speakers.pth')
        ]
        if len(custom_models) != 0:
            yield TestReport.H1("Custom models")
        for custom_model in custom_models:
            yield from self.load_model_and_repr_description('custom/'+custom_model)
            yield from self.test_dub()





