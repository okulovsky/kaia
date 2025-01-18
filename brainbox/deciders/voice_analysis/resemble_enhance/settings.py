from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class ResembleEnhanceSettings:
    connection = ConnectionSettings(20104)

