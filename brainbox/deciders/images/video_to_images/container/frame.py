from typing import *
from dataclasses import dataclass

@dataclass
class Frame:
    frame: Any
    index: int = 0
    timestamp_in_ms: float = 0
    laplacian: float = 0
    comparator_delta: float = 0
    filename: str|None = None
