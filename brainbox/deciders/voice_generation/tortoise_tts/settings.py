from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class TortoiseTTSSettings:
    connection = ConnectionSettings(20203, 60)



