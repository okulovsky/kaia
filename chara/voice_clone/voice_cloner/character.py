from dataclasses import dataclass
from pathlib import Path
from yo_fluq import *

@dataclass
class Character:
    name: str
    samples_folder: Path

    def get_voice_samples(self) -> list[Path]:
        return Query.folder(self.samples_folder).to_list()
