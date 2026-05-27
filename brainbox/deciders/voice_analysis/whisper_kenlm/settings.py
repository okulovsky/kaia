from dataclasses import dataclass
from ....framework import ConnectionSettings


@dataclass
class WhisperKenLMSettings:
    connection = ConnectionSettings(20103, 180)
