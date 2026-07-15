from dataclasses import dataclass
from .model import RhasspyKaldiModel

@dataclass
class RhasspyKaldiSettings:
    languages: tuple[str,...] = (
        RhasspyKaldiModel('en'),
        RhasspyKaldiModel('de'),
    )
