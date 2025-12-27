from typing import Iterable, Iterator

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

    def __getitem__(self, index: int) -> WavWrap:
        return self.wavs[index]

    def __len__(self) -> int:
        return len(self.wavs)

    def __iter__(self) -> Iterator[WavWrap]:
        return iter(self.wavs)

    def clone_for_other_set(self, other_set: Iterable[IDrawable]) -> 'IDrawableCollection':
        return WavList(list(other_set))