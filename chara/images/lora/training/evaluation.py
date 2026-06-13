from dataclasses import dataclass,field

from brainbox.deciders import ComfyUI
from brainbox.deciders.images.comfyui.workflows import TextToImage
from .training import DownloadedCheckpoint
from chara import BrainBoxCasePipeline, CaseCollection
from pathlib import Path
from chara import Chara
from ...common import IImageScenario, assemble_tags


@dataclass
class SceneTags:
    scene_tags: str|None = None
    general_description: str|None = None
    negative_tags: str|None = None

@dataclass
class CharacterTags:
    positive_tags: str|None = None
    negative_tags: str|None = None

    @property
    def repr(self) -> str:
        return f'{self.positive_tags}/{self.negative_tags}'

@dataclass
class EvaluationCase(IImageScenario):
    base_model: str
    lora: DownloadedCheckpoint
    trigger_word: str
    scene: SceneTags = field(default_factory=SceneTags)
    character: CharacterTags = field(default_factory=CharacterTags)
    style_lora: str|None = None
    character_lora_weight: float = 1
    style_lora_weight: float = 1
    image: Path|None = None

    def to_workflow(self) -> TextToImage:
        prompt = assemble_tags(self.scene.general_description, self.trigger_word, self.character.positive_tags, self.scene.scene_tags)
        negative_prompt = assemble_tags(self.scene.negative_tags, self.character.negative_tags)
        task = TextToImage(
            prompt,
            negative_prompt,
            self.base_model,
            width=1024,
            height=1024,
            lora_01=self.lora.checkpoint.filename,
            lora_02=self.style_lora,
            strength_01=self.character_lora_weight,
            strength_02=self.style_lora_weight,
        )
        return task

    @staticmethod
    def case_to_upload(case: 'EvaluationCase'):
        return BrainBoxCasePipeline.Uploader.ResourceUpload(
            ComfyUI,
            'models/loras/'+case.lora.checkpoint.filename,
            case.lora.path
        )

    @staticmethod
    def evaluate(cases: CaseCollection['EvaluationCase']):
        uploader = BrainBoxCasePipeline.Uploader(EvaluationCase.case_to_upload)
        pipe = BrainBoxCasePipeline(EvaluationCase.to_workflow, 'image', result_to_file=True, uploader = uploader)
        cases = Chara.call(pipe)(cases)
        return cases



