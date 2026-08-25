from brainbox.deciders.images.comfyui.workflows import IWorkflow
from dataclasses import dataclass, field, fields
import numpy as np
import json
from pathlib import Path


@dataclass
class KreaTextToImage(IWorkflow):
    prompt: str
    width: int = 1024
    height: int = 1024
    batch_size: int = 1
    seed: int = field(default_factory=lambda: np.random.randint(0, 1000000))
    steps: int = 8
    cfg: float = 1
    sampler_name: str = 'er_sde'
    scheduler: str = 'simple'
    denoise: float = 1.0
    filename_prefix: str = 'krea2/i'
    base_model: str = 'krea-2-turbo-fp8.safetensors'
    clip_name: str = 'qwen3vl_4b_fp8_scaled.safetensors'
    vae_name: str = 'qwen_image_vae.safetensors'
    lora_01: str|None = 'krea2_identity_edit_v1.safetensors'
    strength_01: float = 1.0
    lora_02: str|None = None
    strength_02: float = 1.0
    lora_03: str|None = None
    strength_03: float = 1.0
    lora_04: str|None = None
    strength_04: float = 1.0

    def __post_init__(self):
        for i in range(1, 5):
            name = f'lora_0{i}'
            if getattr(self, name) is None:
                setattr(self, name, "None")

    def create_workflow(self):
        js = json.loads((Path(__file__).parent / 'krea_text_to_image.json').read_text())

        IWorkflow.make_substitution(js, 'text', self.prompt, 'Positive Prompt')
        IWorkflow.make_substitution(js, 'unet_name', self.base_model, 'Load Diffusion Model')

        for f in fields(KreaTextToImage):
            if f.name not in ['prompt', 'base_model']:
                IWorkflow.make_substitution(js, f.name, getattr(self, f.name))

        return js

    def get_ordering_token(self) -> str | None:
        return f"{self.base_model}/{self.lora_01}/{self.lora_02}/{self.lora_03}/{self.lora_04}"

    def create_file_arguments(self):
        return []
