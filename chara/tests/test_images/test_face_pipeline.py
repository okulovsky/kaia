from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from chara.common import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.common.descriptions.characters.appearance import Appearance
from chara.images.generation.scenarios import PipelineFactory, ImageScenarioSettings
from chara.images.generation.scenarios.case import ImageScenarioCase
from chara.images.generation.scenarios.core import ImageContext, Theme
from foundation_kaia.misc import Loc


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: dict | None = None, num_predict: int | None = None) -> str:
        return "happy, smiling"


def _make_case():
    context = ImageContext(base_model='test_model')
    character = Character(
        name='Miku',
        gender=Character.Gender.Feminine,
        description='A cheerful anime girl with teal hair.',
        appearance=Appearance(clothing='casual', colors='teal and white'),
    )
    theme = Theme(name='Daily life')
    case = ImageScenarioCase(context=context, character=character, theme=theme)
    case.activity = 'Playing volleyball at the beach'
    return case


class FacePipelineTestCase(TestCase):
    def test_pipeline_sets_face(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_face_pipeline()
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
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_face_pipeline()
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
