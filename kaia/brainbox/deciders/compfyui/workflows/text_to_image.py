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
    lora_name: str|None =field(default=None, metadata=TemplateWorkflow.meta(is_model_with_priority=1))



    def after_substitution(self, js):
        if self.lora_name is None:
            lora_node = self.find_single_node_by_title(js, "Load LoRA")
            self.find_single_node_by_title(js,"KSampler")['inputs']['model'] = lora_node['inputs']['model']
            for title in ['CLIP Text Encode (Positive)', 'CLIP Text Encode (Negative)']:
                self.find_single_node_by_title(js, title)['inputs']['clip'] = lora_node['inputs']['clip']
            key = self.find_id_by_title(js, 'Load LoRA')
            del js[key[0]]

