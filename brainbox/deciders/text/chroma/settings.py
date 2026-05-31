from dataclasses import dataclass
from ....framework import ConnectionSettings


@dataclass
class ChromaSettings:
    connection = ConnectionSettings(20010, 60)
