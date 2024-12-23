from dataclasses import dataclass
from kaia.infra import Loc
from ....framework import ConnectionSettings

@dataclass
class TortoiseTTSSettings:
    connection = ConnectionSettings(20203, 60)



