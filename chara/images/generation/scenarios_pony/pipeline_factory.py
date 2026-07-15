from chara import CaseCollection, Chara
from .settings import ImageScenarioSettings
from pathlib import Path
from chara.common.tools.llm import JinjaPrompter, PromptTaskBuilder, BulletPointDivider, parse_json
from chara.common import BrainBoxCasePipeline
from .case import ImageScenarioCase, Scene
from .shot import Shot
from .tag_matching import TagMatchingPipeline
from .clothing import Clothing


class PipelineFactory:
    def __init__(self,
                 settings: ImageScenarioSettings,
                 ):
        self.settings = settings


    def create_task_builder(self, template: Path):
        prompter = JinjaPrompter(
            template,
            (Path(__file__).parent,),
            dict(settings = self.settings)
        )
        return PromptTaskBuilder(self.settings.llm, prompter)


    def get_activity_pipeline(self):
        return BrainBoxCasePipeline(
            self.create_task_builder(Path(__file__).parent/'activity.jinja'),
            'activity',
            BulletPointDivider()
        )


    def activity_to_tags_pipeline(self, cases: CaseCollection[ImageScenarioCase]) -> CaseCollection[ImageScenarioCase]:
        pipe = TagMatchingPipeline(
            self.settings.tags_collection,
            'activity',
            'activity_tags',
            self.settings.tags_per_activity
        )
        cases = Chara.call(pipe)(cases.successes_collection)
        return cases.successes_collection

    def _set_scene(self, case: ImageScenarioCase, result: str):
        js = parse_json(result)
        fixed_js = {}
        for key, value in js.items():
            fixed_js[key] = value[:self.settings.tags_per_scene_attribute]
        case.scene = Scene(**fixed_js)


    def get_scene_pipeline(self):
        return BrainBoxCasePipeline(
            self.create_task_builder(Path(__file__).parent/'scene.jinja'),
            self._set_scene,
        )


    def _set_clothing(self, case: ImageScenarioCase, result: str):
        js = parse_json(result)
        case.clothing = Clothing(**js)

    def get_clothing_pipeline(self):
        return BrainBoxCasePipeline(
            self.create_task_builder(Path(__file__).parent/'clothing.jinja'),
            self._set_clothing
        )

    def get_face_pipeline(self):
        return BrainBoxCasePipeline(
            self.create_task_builder(Path(__file__).parent/'face.jinja'),
            'face'
        )
