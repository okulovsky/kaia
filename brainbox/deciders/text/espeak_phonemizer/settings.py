from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class EspeakPhonemizerSettings:
    connection = ConnectionSettings(20001)
