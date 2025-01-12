from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import RhasspyKaldiModel

@dataclass
class RhasspyKaldiSettings:
    connection = ConnectionSettings(20101)
    languages: tuple[str,...] = (
        RhasspyKaldiModel('en'),
        RhasspyKaldiModel('de'),
    )
