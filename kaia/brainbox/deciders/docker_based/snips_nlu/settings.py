from dataclasses import dataclass
from pathlib import Path
from kaia.infra import Loc

@dataclass
class SnipsNLUSettings:
    address: str = '127.0.0.1'
    image_name: str = 'snips-nlu'
    port: int = 11005
    data_folder: Path = Loc.deciders_resources_folder / 'snips_nlu'