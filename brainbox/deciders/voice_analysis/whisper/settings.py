from dataclasses import dataclass
from enum import Enum


class WhisperModels(str, Enum):
    base = 'base'


@dataclass
class WhisperSettings:
    models_to_install = [WhisperModels.base]
