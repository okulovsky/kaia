from __future__ import annotations
from chara.common import ICase
from pathlib import Path
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING
from brainbox import BrainBox

if TYPE_CHECKING:
    from .voice_train import VoiceTrain


class VoiceModel:
    def get_metadata(self) -> dict:
        return copy(self.__dict__)


@dataclass
class VoiceTrainMetadata:
    model_name: str|None = None
    original_samples_path: Path|None = None


@dataclass
class VoiceTrainCase(ICase):
    trainer: VoiceTrain
    source: Path
    recoded_samples: list[Path]|None = None
    train_samples: list[Path]|None = None
    leveled_samples: list[Path]|None = None
    task: BrainBox.Task|None = None
    model: VoiceModel|None = None
