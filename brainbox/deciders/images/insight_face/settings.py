from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class InsightFaceSettings:
    connection = ConnectionSettings(20304)
