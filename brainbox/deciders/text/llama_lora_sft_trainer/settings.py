from dataclasses import dataclass
from brainbox.framework import ConnectionSettings


@dataclass
class LlamaLoraSFTTrainerSettings:
    connection = ConnectionSettings(20404)
