import json
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


SCENE_RESPONSE = json.dumps({
    "position": ["standing", "holding bottle", "leaning on counter", "arms relaxed"],
    "environment": ["dim light", "champagne bottle", "neon signs", "bar counter"],
})


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: Ollama.Options | None = None, image=None) -> str:
        return SCENE_RESPONSE


def _make_case(tags_per_scene_attribute: int = 3):
    settings = PonySettings(
        template=TextToImage(prompt='', negative_prompt='', model='test_model'),
        tags_per_scene_attribute=tags_per_scene_attribute,
    )
    character = Character(
        name='Miku',
        gender=Character.Gender.Feminine,
        description='A cheerful anime girl with teal hair.',
        appearance=Appearance(clothing='casual', colors='teal and white'),
    )
    theme = Theme('Daily life')
    case = PonyCase(character=character, settings=settings, theme=theme)
    case.activity = 'Cooking stew in the kitchen'
    case.activity_tags = ('standing', 'kitchen', 'stew pot')
    return case


def _make_factory():
    return PonyPipelineFactory('mistral-small', ())


class ScenePipelineTestCase(TestCase):
    def test_pipeline_sets_scene(self):
        factory = _make_factory()
        pipeline = factory.get_scene_pipeline()
        input_cases = CaseCollection([_make_case()])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        cases = result.cases
        self.assertEqual(1, len(cases))
        scene = cases[0].scene
        self.assertIsNotNone(scene)
        # Default tags_per_scene_attribute=3, so first 3 items from each list
        self.assertEqual(['standing', 'holding bottle', 'leaning on counter'], scene.position)
        self.assertEqual(['dim light', 'champagne bottle', 'neon signs'], scene.environment)

    def test_pipeline_truncates_to_tags_per_scene_attribute(self):
        factory = _make_factory()
        pipeline = factory.get_scene_pipeline()
        input_cases = CaseCollection([_make_case(tags_per_scene_attribute=2)])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipeline)(input_cases)

        scene = result.cases[0].scene
        self.assertEqual(2, len(scene.position))
        self.assertEqual(2, len(scene.environment))
        self.assertEqual(['standing', 'holding bottle'], scene.position)
        self.assertEqual(['dim light', 'champagne bottle'], scene.environment)
