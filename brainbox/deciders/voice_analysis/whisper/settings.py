from dataclasses import dataclass
from enum import Enum
from ....framework import ConnectionSettings


class WhisperModels(str, Enum):
    base = 'base'


@dataclass
class WhisperSettings:
    connection = ConnectionSettings(20102)
    models_to_install = [WhisperModels.base]
