from brainbox.deciders.images.comfyui.workflows import IWorkflow
from dataclasses import dataclass, field, fields
import numpy as np
import json
from pathlib import Path
from foundation_kaia.marshalling import FileLike

@dataclass
class KreaImageToImage(IWorkflow):
    source_image: FileLike
    prompt: str
    source_image_2: FileLike | None = None
    negative_prompt: str = ''
    width: int = 1024
    height: int = 1024
    batch_size: int = 1
    seed: int = field(default_factory=lambda:np.random.randint(0, 1000000))
    steps: int = 8
    cfg: float = 1
    sampler_name: str = 'euler'
    scheduler: str = 'normal'
    denoise: float = 1.0
    source_image_size_increase: float = 8
    base_model: str = 'krea-2-turbo-bf16.safetensors'
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
        for i in range(1,5):
            name = f'lora_0{i}'
            if getattr(self, name) is None:
                setattr(self, name, "None")


    def create_workflow(self):
        js = json.loads((Path(__file__).parent / 'krea_image_to_image.json').read_text())
        IWorkflow.make_substitution(js, 'prompt', self.prompt, 'Krea2 Edit (grounded encode) Positive Prompt')
        IWorkflow.make_substitution(js, 'prompt', self.negative_prompt, 'Krea2 Edit (grounded encode) Negative Prompt')
        IWorkflow.make_substitution(js, 'image', IWorkflow.input_placeholder(0), 'Load Image 1')
        IWorkflow.make_substitution(js, 'unet_name', self.base_model, 'Load Diffusion Model')

        for i in range(2):
            IWorkflow.make_substitution(js, 'resize_type.multiple', self.source_image_size_increase, f'Second Resize Image {i+1}')

        if self.source_image_2 is not None:
            IWorkflow.make_substitution(js, 'image', IWorkflow.input_placeholder(1), 'Load Image 2')
        else:
            IWorkflow.trim_nodes(js, lambda node: node['_meta']['title'].endswith('Image 2'))

        for f in fields(KreaImageToImage):
            if f.name not in ['source_image', 'source_image_2', 'prompt', 'negative_prompt', 'base_model', 'source_image_size_increase']:
                IWorkflow.make_substitution(js, f.name, getattr(self, f.name))

        return js

    def get_ordering_token(self) -> str | None:
        return f"{self.base_model}/{self.lora_01}/{self.lora_02}/{self.lora_03}/{self.lora_04}"

    def create_file_arguments(self):
        if self.source_image_2 is not None:
            return [self.source_image, self.source_image_2]
        return [self.source_image]