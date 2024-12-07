from .template import TemplateWorkflow
from dataclasses import dataclass, field
import numpy as np
import pprint

@dataclass
class TextToImage(TemplateWorkflow):
    prompt: str = field(metadata=TemplateWorkflow.meta('text', 'CLIP Text Encode (Positive)'))
    negative_prompt: str = field(default='', metadata=TemplateWorkflow.meta('text', 'CLIP Text Encode (Negative)'))
    width: int = 512
    height: int = 512
    batch_size: int = 1
    seed: int = field(default_factory=lambda:np.random.randint(0, 1000000))
    steps: int = 20
    cfg: float = 8
    sampler_name: str = 'euler'
    scheduler: str = 'normal'
    denoise: float = 1.0
    model: str = field(default='v1-5-pruned-emaonly.ckpt', metadata=TemplateWorkflow.meta('ckpt_name', is_model_with_priority=0))
    filename_prefix: str = field(default='', metadata=TemplateWorkflow.meta(maps_to_job_id=True))
    lora_01: str|None = field(default="None", metadata=TemplateWorkflow.meta(is_model_with_priority=1))
    strength_01: float = 1.0
    lora_02: str|None = field(default="None", metadata=TemplateWorkflow.meta(is_model_with_priority=1))
    strength_02: float = 1.0
    lora_03: str|None = field(default="None", metadata=TemplateWorkflow.meta(is_model_with_priority=1))
    strength_03: float = 1.0
    lora_04: str|None = field(default="None", metadata=TemplateWorkflow.meta(is_model_with_priority=1))
    strength_04: float = 1.0



