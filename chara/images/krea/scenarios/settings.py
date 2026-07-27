from dataclasses import dataclass
from ..workflow import KreaImageToImage

@dataclass
class KreaSettings:
    workflow_template: KreaImageToImage
    name_to_source_filename_template: str = '{}.png'
    activity_template: str = "Draw this character doing {}"
    prompt_suffix: str|None = None
