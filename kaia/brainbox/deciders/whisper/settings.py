from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path

@dataclass
class WhisperSettings:
    port: int = 11004
    models_to_download: tuple[str,...] = (
        'base',
    )
    startup_time_in_seconds: int = 15
    autoload_model: None|str = None
