from dataclasses import dataclass
from ....framework import ConnectionSettings


@dataclass
class WhisperXSettings:
    connection = ConnectionSettings(20106, 300)
