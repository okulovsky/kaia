from __future__ import annotations
from dataclasses import dataclass
from .read_and_write import WavInfo, read_wav, write_wav
from .slicing import slice_wav_by_seconds
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..wav_wrap import WavWrap

@dataclass
class WavEditable:
    info: WavInfo
    data: np.ndarray

    @staticmethod
    def from_bytes(content: bytes):
        info, data = read_wav(content)
        return WavEditable(info, data)

    @property
    def n_frames(self) -> int:
        """Number of frames inferred from data."""
        return self.data.shape[0]

    @property
    def n_channels(self) -> int:
        """Number of channels inferred from data/info."""
        return self.data.shape[1]

    @property
    def duration_sec(self) -> float:
        """Duration in seconds inferred from n_frames and frame_rate."""
        sr = self.info.frame_rate
        return self.n_frames / sr if sr else 0.0

    def to_bytes(self) -> bytes:
        return write_wav(self.info, self.data)

    def to_wav(self) -> WavWrap:
        from ..wav import Wav
        return Wav.one(self.to_bytes())


    def __getitem__(self, sl: slice) -> "WavEditable":
        return WavEditable(
            self.info,
            slice_wav_by_seconds(self.data, self.info, sl)
        )