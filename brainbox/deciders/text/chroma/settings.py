from dataclasses import dataclass

from brainbox.framework import ConnectionSettings

@dataclass
class ChromaSettings:
    connection = ConnectionSettings(5252, 180)