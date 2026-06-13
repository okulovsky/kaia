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


# 'cowboy shot' is ShotSettings.framing[0], so it maps to None in composition
SHOT_RESPONSE_WITH_DEFAULT_FRAMING = json.dumps({
    "framing": "cowboy shot",
    "character_angle": "side view",
    "camera_angle": "high angle",
})

SHOT_RESPONSE_NON_DEFAULT = json.dumps({
    "framing": "full body shot",
    "character_angle": "back view",
    "camera_angle": "low angle",
})


class OllamaDefaultMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: dict | None = None, num_predict: int | None = None) -> str:
        return SHOT_RESPONSE_WITH_DEFAULT_FRAMING


class OllamaNonDefaultMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: dict | None = None, num_predict: int | None = None) -> str:
        return SHOT_RESPONSE_NON_DEFAULT


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
    case.activity = 'Cooking stew in the kitchen'
    return case


class ShotPipelineTestCase(TestCase):
    def test_default_framing_becomes_none(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_shot_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaDefaultMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        composition = result.cases[0].composition
        self.assertIsNotNone(composition)
        self.assertIsNone(composition.framing)
        self.assertEqual('side view', composition.character_angle)
        self.assertEqual('high angle', composition.camera_angle)

    def test_non_default_values_are_preserved(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_shot_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaNonDefaultMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        composition = result.cases[0].composition
        self.assertIsNotNone(composition)
        self.assertEqual('full body shot', composition.framing)
        self.assertEqual('back view', composition.character_angle)
        self.assertEqual('low angle', composition.camera_angle)
