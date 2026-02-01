from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class CosyVoiceSettings:
    connection = ConnectionSettings(20001, 120)
