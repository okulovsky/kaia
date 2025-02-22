from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class ZonosSettings:
    connection = ConnectionSettings(20001, 20)
