from .template import TemplateWorkflow
from dataclasses import dataclass, field
from ...arch.utils import FileLike

@dataclass
class Upscale(TemplateWorkflow):
    input_filename: FileLike.Type = field(metadata=TemplateWorkflow.meta('image','Load Image', is_input_file=True))
    model_name: str = field(default='4x-AnimeSharp.pth', metadata=TemplateWorkflow.meta(is_model_with_priority=0))
    width: int = field(default=1024, metadata=TemplateWorkflow.meta(node_title='Upscale Image'))
    height: int = field(default=1024, metadata=TemplateWorkflow.meta(node_title='Upscale Image'))
    filename_prefix: str = field(default='', metadata=TemplateWorkflow.meta(maps_to_job_id=True))




