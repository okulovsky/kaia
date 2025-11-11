from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class ChatterboxSettings:
    connection = ConnectionSettings(20001, 120)
