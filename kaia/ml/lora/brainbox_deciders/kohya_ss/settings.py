from dataclasses import dataclass
from pathlib import Path

@dataclass
class KohyaSSSettings:
    custom_models_folder: Path|None = None
    loras_models_folder: Path|None = None
    port: int = 11012
