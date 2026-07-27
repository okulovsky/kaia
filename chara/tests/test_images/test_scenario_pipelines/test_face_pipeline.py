from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Ollama
from chara.common import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.common.descriptions.characters.appearance import Appearance
from brainbox.deciders.images.comfyui.workflows import TextToImage
from chara.images.pony.scenarios import PonyCase, PonySettings, PonyPipelineFactory
from chara.images.common import Theme
from foundation_kaia.misc import Loc


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: Ollama.Options | None = None, image=None) -> str:
        return "happy, smiling"


def _make_case():
    settings = PonySettings(template=TextToImage(prompt='', negative_prompt='', model='test_model'))
    character = Character(
        name='Miku',
        gender=Character.Gender.Feminine,
        description='A cheerful anime girl with teal hair.',
        appearance=Appearance(clothing='casual', colors='teal and white'),
    )
    theme = Theme('Daily life')
    case = PonyCase(character=character, settings=settings, theme=theme)
    case.activity = 'Playing volleyball at the beach'
    return case


def _make_factory():
    return PonyPipelineFactory('mistral-small', ())


class FacePipelineTestCase(TestCase):
    def test_pipeline_sets_face(self):
        factory = _make_factory()
        pipeline = factory.create_face_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        cases = result.cases
        self.assertEqual(1, len(cases))
        self.assertEqual('happy, smiling', cases[0].face)

    def test_pipeline_processes_multiple_cases(self):
        factory = _make_factory()
        pipeline = factory.create_face_pipeline()
        input_cases = CaseCollection([_make_case(), _make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        cases = result.cases
        self.assertEqual(2, len(cases))
        for case in cases:
            self.assertEqual('happy, smiling', case.face)
