from .wav_wrap import WavWrap
from dataclasses import dataclass, field
from ..core import IDrawableCollection
from collections.abc import Iterator

@dataclass
class WavList(IDrawableCollection[WavWrap]):
    wavs: list[WavWrap] = field(default_factory=list)

    def __add__(self, other: 'WavList') -> 'WavList':
        return WavList(self.wavs + other.wavs)

    def __getitem__(self, index: int) -> WavWrap:
        return self.wavs[index]

    def __len__(self) -> int:
        return len(self.wavs)

    def __iter__(self) -> Iterator[WavWrap]:
        return iter(self.wavs)

