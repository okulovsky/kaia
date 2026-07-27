from dataclasses import dataclass, field
from brainbox.deciders.images.comfyui.workflows import TextToImage

@dataclass
class PonySettings:
    template: TextToImage
    positive_prompt: str|None = None
    negative_prompt: str | None = None
    name_to_keyword_template: str|None = None
    name_to_lora_file_template: str|None = None
    tags_collection: str = 'CharaImageTags'
    tags_per_activity: int = 30
    tags_per_scene_attribute: int = 3


