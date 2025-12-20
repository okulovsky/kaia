from typing import Iterable

from ..core import IDrawableCollection, IDrawable
from .wav_wrap import WavWrap
from dataclasses import dataclass, field

@dataclass
class WavList(IDrawableCollection):
    wavs: list[WavWrap] = field(default_factory=list)

    def get_drawables(self) -> Iterable[IDrawable]:
        return self.wavs

    def __add__(self, other: 'WavList') -> 'WavList':
        return WavList(self.wavs + other.wavs)