from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class BoilerplateServerSettings:
    connection = ConnectionSettings(20001, 20)
