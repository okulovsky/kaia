from pathlib import Path

from chara.common.llm import BrainBoxLLMEngine, ILLMBuilder, LLMSetup
from chara import BrainBoxCasePipeline
from .clothing import Clothing
from .scene import Scene


class PipelineFactory:
    def __init__(self, llm_model: str, script_folders: tuple[Path,...]):
        self.llm_model = llm_model
        self.script_folders = script_folders + (Path(__file__).parent,)
        self.setup = LLMSetup(BrainBoxLLMEngine(), llm_model)

    def create_request_builder(self, template_name: str, t: type|None = None, temperature: float|None = None) -> ILLMBuilder:
        builder = (self.setup
                   .default()
                   .template(template_name, self.script_folders)
                   .options(temperature=temperature))
        if t is not None:
            builder = builder.result_type(t)
        return builder

    def create_clothing_pipeline(self, temperature: float|None = None) -> BrainBoxCasePipeline:
        return (self
                .create_request_builder('clothing.jinja', Clothing, temperature)
                .assign('clothing')
                .to_request()
                .create_brainbox_pipeline())

    def create_face_pipeline(self, temperature: float|None = None) -> BrainBoxCasePipeline:
        return (self
                .create_request_builder('face.jinja', temperature=temperature)
                .assign('face')
                .to_request()
                .create_brainbox_pipeline())

    def create_scene_pipeline(self, temperature: float|None = None) -> BrainBoxCasePipeline:
        return (self
                .create_request_builder('scene.jinja', Scene, temperature)
                .assign('scene')
                .to_request()
                .create_brainbox_pipeline())
