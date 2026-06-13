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
        return (
            "* Cooking stew in the kitchen\n"
            "* Reading a book in the library\n"
            "* Walking in the park"
        )


def _make_case():
    context = ImageContext(base_model='test_model')
    character = Character(
        name='Miku',
        gender=Character.Gender.Feminine,
        description='A cheerful anime girl with teal hair.',
        appearance=Appearance(clothing='casual', colors='teal and white'),
    )
    theme = Theme(name='Daily life')
    return ImageScenarioCase(context=context, character=character, theme=theme)


class ActivityPipelineTestCase(TestCase):
    def test_pipeline_expands_case_into_activities(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_activity_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        cases = result.cases
        self.assertEqual(3, len(cases))
        activities = [c.activity for c in cases]
        self.assertIn('Cooking stew in the kitchen', activities)
        self.assertIn('Reading a book in the library', activities)
        self.assertIn('Walking in the park', activities)

    def test_pipeline_expands_multiple_input_cases(self):
        factory = PipelineFactory(ImageScenarioSettings())
        pipeline = factory.get_activity_pipeline()
        input_cases = CaseCollection([_make_case(), _make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        # 2 input cases × 3 activities each = 6 output cases
        self.assertEqual(6, len(result.cases))
        for case in result.cases:
            self.assertIsNotNone(case.activity)
