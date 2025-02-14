from typing import *
from dataclasses import dataclass
from PIL import Image

@dataclass
class Frame:
    frame: Any
    pil_image: Image.Image
    index: int = 0
    timestamp_in_ms: float = 0
    laplacian: float = 0
    semantic_comparator_delta: float = 0
    simple_comparator_delta: float = 0
    filename: str|None = None
