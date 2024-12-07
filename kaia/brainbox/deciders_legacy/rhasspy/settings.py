from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path

@dataclass
class RhasspySettings:
    profile: Path = Path(__file__).parent/'files/default_profile.json'
    port: int = 12101
    startup_timeout_in_seconds = 15
    custom_words: None|dict[str,str] = None





