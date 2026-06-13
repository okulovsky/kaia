from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from chara.common import Chara, CaseCollection
from chara.common.descriptions.characters import Character
from chara.common.descriptions.characters.appearance import Appearance
from chara.images.generation.scenarios import PipelineFactory, ImageScenarioSettings
from chara.images.generation.scenarios.case import ImageScenarioCase
from chara.images.generation.scenarios.core import ImageContext, Theme
from foundation_kaia.misc import Loc


class ChromaMock(ISelfManagingDecider):
    def get_name(self):
        return "Chroma"

    def find_neighbors(self, text: str, k: int = 5, collection_name: str | None = None) -> list[dict]:
        return [
            {'text': 'cooking'},
            {'text': 'kitchen'},
            {'text': 'stew pot'},
        ]


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


class ActivityToTagsPipelineTestCase(TestCase):
    def test_pipeline_sets_activity_tags(self):
        factory = PipelineFactory(ImageScenarioSettings())
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([ChromaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = factory.activity_to_tags_pipeline(input_cases)

        cases = result.cases
        self.assertEqual(1, len(cases))
        self.assertEqual(('cooking', 'kitchen', 'stew pot'), cases[0].activity_tags)

    def test_pipeline_processes_multiple_cases(self):
        factory = PipelineFactory(ImageScenarioSettings())
        input_cases = CaseCollection([_make_case(), _make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([ChromaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = factory.activity_to_tags_pipeline(input_cases)

        cases = result.cases
        self.assertEqual(2, len(cases))
        for case in cases:
            self.assertEqual(('cooking', 'kitchen', 'stew pot'), case.activity_tags)
