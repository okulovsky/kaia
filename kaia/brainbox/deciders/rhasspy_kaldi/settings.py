from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path

@dataclass
class RhasspyKaldiSettings:
    port: int = 11009
    startup_timeout_in_seconds = 15
    languages: tuple[str,...] = ('en','de')
