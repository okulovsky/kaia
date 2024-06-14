from dataclasses import dataclass
from .....infra import Loc
from pathlib import Path

@dataclass
class WhisperSettings:
    address: str = '127.0.0.1'
    port: int = 11004
    models_to_download: tuple[str,...] = (
        'base',
    )
    default_model: str = 'base'
    image_name: str = 'whisper-stt'
    use_gpu: bool = False
    data_folder: Path = Loc.deciders_resources_folder/'whisper'