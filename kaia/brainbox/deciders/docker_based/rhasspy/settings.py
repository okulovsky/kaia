from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path

@dataclass
class RhasspySettings:
    folder: Path = Loc.deciders_resources_folder/'rhasspy'
    profile: Path = Path(__file__).parent/'files/default_profile.json'
    propagate_sound_device: bool = False
    port: int = 12101
    address: str = '127.0.0.1'


