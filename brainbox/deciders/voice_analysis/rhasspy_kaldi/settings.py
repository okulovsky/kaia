from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class RhasspyKaldiSettings:
    connection = ConnectionSettings(20101, 15)
    languages: tuple[str,...] = ('en','de')
