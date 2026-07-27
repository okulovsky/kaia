from chara import CaseCollection, Chara
from pathlib import Path
from chara.common.tools.llm import parse_json
from chara.common import BrainBoxCasePipeline
from .case import PonyCase
from ...common import PipelineFactory, Scene
from .tag_matching import TagMatchingPipeline


class PonyPipelineFactory(PipelineFactory):
    def __init__(self, llm_model: str, scripts_folder: tuple[Path,...]):
        super().__init__(llm_model, scripts_folder+(Path(__file__).parent,))

    def _get_collection_name(self, case: PonyCase):
        return case.settings.tags_collection

    def _get_activity(self, case: PonyCase):
        return case.activity

    def _get_tag_count(self, case: PonyCase):
        return case.settings.tags_per_activity

    def activity_to_tags_pipeline(self, cases: CaseCollection[PonyCase]) -> CaseCollection[PonyCase]:
        pipe = TagMatchingPipeline(
            self._get_collection_name,
            self._get_activity,
            self._get_tag_count,
            'activity_tags',
        )
        cases = Chara.call(pipe)(cases.successes_collection)
        return cases.successes_collection

    def _set_scene(self, case: PonyCase, result: str):
        js = parse_json(result)
        fixed_js = {}
        for key, value in js.items():
            fixed_js[key] = value[:case.settings.tags_per_scene_attribute]
        case.scene = Scene(**fixed_js)

    def get_scene_pipeline(self):
        return BrainBoxCasePipeline(
            self.create_task_builder('scene.jinja'),
            self._set_scene,
        )




