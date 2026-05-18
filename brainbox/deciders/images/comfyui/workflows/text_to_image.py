from .workflow import IWorkflow
from dataclasses import dataclass, field, fields
import numpy as np
import json
from pathlib import Path

@dataclass
class TextToImage(IWorkflow):
    prompt: str
    negative_prompt: str
    model: str
    width: int = 512
    height: int = 512
    batch_size: int = 1
    seed: int = field(default_factory=lambda:np.random.randint(0, 1000000))
    steps: int = 20
    cfg: float = 8
    sampler_name: str = 'euler'
    scheduler: str = 'normal'
    denoise: float = 1.0
    lora_01: str|None = None
    strength_01: float = 1.0
    lora_02: str|None = None
    strength_02: float = 1.0
    lora_03: str|None = None
    strength_03: float = 1.0
    lora_04: str|None = None
    strength_04: float = 1.0

    def __post_init__(self):
        for i in range(1,5):
            name = f'lora_0{i}'
            if getattr(self, name) is None:
                setattr(self, name, "None")


    def create_workflow(self):
        js = json.loads((Path(__file__).parent / 'text_to_image.json').read_text())
        IWorkflow.make_substitution(js, 'text', self.prompt, 'CLIP Text Encode (Positive)')
        IWorkflow.make_substitution(js, 'text', self.negative_prompt, 'CLIP Text Encode (Negative)')
        IWorkflow.make_substitution(js, 'ckpt_name', self.model, 'Load Checkpoint')

        for field in fields(TextToImage):
            if field.name not in ['prompt', 'negative_prompt', 'model']:
                IWorkflow.make_substitution(js, field.name, getattr(self, field.name))

        return js

    def get_ordering_token(self) -> str | None:
        return f"{self.model}/{self.lora_01}/{self.lora_02}/{self.lora_03}/{self.lora_04}"

    def create_file_arguments(self):
        return []




