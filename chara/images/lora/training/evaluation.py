from dataclasses import dataclass

from brainbox.deciders import ComfyUI
from brainbox.deciders.images.comfyui.workflows import TextToImage
from .training import DownloadedCheckpoint
from brainbox.deciders.images.one_trainer import OneTrainer
from chara import BrainBoxCasePipeline
from pathlib import Path
from chara import Chara, ICase

@dataclass
class Scene:
    general_description: str
    character_tags: str
    scene_tags: str
    negative_tags: str

@dataclass
class EvaluationCase(ICase):
    scene: Scene
    base_model: str
    lora: DownloadedCheckpoint
    style_lora: str|None = None
    image: Path|None = None

def case_to_task(case: EvaluationCase):
    prompt = ', '.join(s.strip() for s in [case.scene.general_description, case.scene.character_tags, case.scene.scene_tags])

    task = TextToImage(
        prompt,
        case.scene.negative_tags,
        case.base_model,
        width = 1024,
        height = 1024,
        lora_01= case.lora.checkpoint.filename,
        lora_02 = case.style_lora
    )
    return task

def case_to_upload(case: EvaluationCase):
    return BrainBoxCasePipeline.Uploader.ResourceUpload(
        ComfyUI,
        'models/loras/'+case.lora.checkpoint.filename,
        case.lora.path
    )

def evaluate(cases: list[EvaluationCase]):
    uploader = BrainBoxCasePipeline.Uploader(case_to_upload)
    pipe = BrainBoxCasePipeline(case_to_task, 'image', result_to_file=True, uploader = uploader)
    cases = Chara.call(pipe)(cases)
    return cases



