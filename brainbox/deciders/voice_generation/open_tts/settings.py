from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class OpenTTSSettings:
    connection = ConnectionSettings(20201, 30)
