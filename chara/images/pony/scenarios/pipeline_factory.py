from chara import CaseCollection, Chara
from pathlib import Path
from chara.common.llm import Json
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

    def _parse_scene(self, case: PonyCase, result: str) -> Scene:
        js = Json.parse_object(result)
        fixed_js = {}
        for key, value in js.items():
            fixed_js[key] = value[:case.settings.tags_per_scene_attribute]
        return Scene(**fixed_js)

    def get_scene_pipeline(self) -> BrainBoxCasePipeline:
        return (self
                .create_request_builder('scene.jinja')
                .parse(self._parse_scene)
                .assign('scene')
                .to_request()
                .create_brainbox_pipeline())




