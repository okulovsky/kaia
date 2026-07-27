from pathlib import Path

from brainbox.deciders import Ollama
from chara.common.tools.llm import JinjaPrompter, PromptTaskBuilder, parse_and_assign_json
from chara import BrainBoxCasePipeline
from .clothing import Clothing
from .scene import Scene


class PipelineFactory:
    def __init__(self, llm_model: str, script_folders: tuple[Path,...]):
        self.llm_model = llm_model
        self.script_folders = script_folders + (Path(__file__).parent,)

    def create_task_builder(self, template_name: str, t: type|None = None, temperature: float|None = None):
        prompter = JinjaPrompter(
            template_name,
            self.script_folders,
        )
        return PromptTaskBuilder(self.llm_model, prompter, format_type=t, options=Ollama.Options(temperature=temperature))

    def create_clothing_pipeline(self, temperature: float|None = None):
        return BrainBoxCasePipeline(
            self.create_task_builder('clothing.jinja', Clothing, temperature),
            parse_and_assign_json('clothing', Clothing)
        )

    def create_face_pipeline(self, temperature: float|None = None):
        return BrainBoxCasePipeline(
            self.create_task_builder('face.jinja', temperature=temperature),
            'face'
        )

    def create_scene_pipeline(self, temperature: float|None = None):
        return BrainBoxCasePipeline(
            self.create_task_builder('scene.jinja', Scene, temperature),
            parse_and_assign_json('scene', Scene),
        )



