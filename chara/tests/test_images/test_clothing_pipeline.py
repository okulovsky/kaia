import json
from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from chara.common import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.common.descriptions.characters.appearance import Appearance
from chara.images.generation.scenarios import PipelineFactory, ImageScenarioSettings
from chara.images.generation.scenarios.case import ImageScenarioCase
from chara.images.generation.scenarios.core import ImageContext, Theme
from foundation_kaia.misc import Loc


CLOTHING_RESPONSE = json.dumps({
    "top": ["white tank top"],
    "bottom": ["colorful shorts", "floral pattern"],
    "costume": [],
    "outerwear": [],
    "footwear": ["red sneakers"],
    "headwear": [],
    "accessories": ["sunglasses"],
})


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: dict | None = None, num_predict: int | None = None) -> str:
        return CLOTHING_RESPONSE


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


class ClothingPipelineTestCase(TestCase):
    def test_pipeline_sets_clothing(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_clothing_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        cases = result.cases
        self.assertEqual(1, len(cases))
        clothing = cases[0].clothing
        self.assertIsNotNone(clothing)
        self.assertEqual(['white tank top'], clothing.top)
        self.assertEqual(['colorful shorts', 'floral pattern'], clothing.bottom)
        self.assertEqual([], clothing.costume)
        self.assertEqual(['red sneakers'], clothing.footwear)
        self.assertEqual(['sunglasses'], clothing.accessories)

    def test_pipeline_processes_multiple_cases_without_errors(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_clothing_pipeline()
        input_cases = CaseCollection([_make_case(), _make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        self.assertEqual(2, len(result.cases))
        for case in result.cases:
            self.assertIsNone(case.error)
            self.assertIsNotNone(case.clothing)
