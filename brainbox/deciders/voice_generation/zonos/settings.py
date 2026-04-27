from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class ZonosSettings:
    connection = ConnectionSettings(20206, 20)
