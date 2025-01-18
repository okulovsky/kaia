from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class OpenVoiceSettings:
    connection = ConnectionSettings(20204)

