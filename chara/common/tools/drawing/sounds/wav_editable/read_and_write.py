from dataclasses import dataclass
import io
from typing import Tuple

import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class WavInfo:
    n_channels: int
    sample_width: int          # bytes per sample on disk: 1, 2, 3, 4, 8
    frame_rate: int            # samples per second (per channel)
    comptype: str              # kept for compatibility, typically "NONE"
    compname: str              # usually "not compressed"


def _subtype_to_sample_width(subtype: str) -> int:
    """
    Map soundfile's subtype string to bytes per sample on disk.
    This covers common uncompressed WAV subtypes.
    """
    mapping = {
        "PCM_S8": 1,
        "PCM_U8": 1,
        "PCM_16": 2,
        "PCM_24": 3,
        "PCM_32": 4,
        "FLOAT": 4,   # IEEE float 32-bit
        "DOUBLE": 8,  # IEEE float 64-bit
    }
    try:
        return mapping[subtype]
    except KeyError:
        raise NotImplementedError(
            f"Unsupported WAV subtype: {subtype!r}. "
            f"Supported (uncompressed) subtypes: {', '.join(sorted(mapping))}"
        )


def read_wav(bts: bytes) -> Tuple[WavInfo, np.ndarray]:
    """
    Read a WAV file from bytes using soundfile and return:
      - header info as WavInfo
      - samples as numpy array of shape (n_frames, n_channels), dtype=float32

    Notes:
      * Works with both PCM (16/24/32-bit) and IEEE float (32/64-bit) WAV.
      * Data is always returned as float32 in approximately [-1.0, 1.0].
      * sample_width in WavInfo reflects bytes-per-sample on disk
        (e.g. 2 for PCM_16, 3 for PCM_24, 4 for PCM_32/FLOAT, 8 for DOUBLE).
    """
    bio = io.BytesIO(bts)

    # Open using SoundFile to inspect metadata and read audio
    with sf.SoundFile(bio) as f:
        n_channels = f.channels
        frame_rate = f.samplerate
        subtype = f.subtype  # e.g. "PCM_16", "FLOAT", "PCM_24", ...
        sample_width = _subtype_to_sample_width(subtype)

        # We normalize everything to float32 for downstream processing.
        # always_2d=True ensures shape (n_frames, n_channels)
        data = f.read(dtype="float32", always_2d=True)

    # For all these uncompressed WAV subtypes we can treat "compression type"
    # as NONE for compatibility with the old wave-based API.
    info = WavInfo(
        n_channels=n_channels,
        sample_width=sample_width,
        frame_rate=frame_rate,
        comptype="NONE",
        compname="not compressed",
    )

    return info, data


def _choose_wav_subtype(sample_width: int, dtype: np.dtype) -> str:
    """
    Choose a reasonable WAV subtype for writing, based on desired
    bytes-per-sample and data dtype.

    Rules:
      * sample_width == 2  -> "PCM_16"
      * sample_width == 3  -> "PCM_24"
      * sample_width == 4:
           - float dtype   -> "FLOAT"  (32-bit IEEE float)
           - int dtype     -> "PCM_32"
      * sample_width == 8:
           - float dtype   -> "DOUBLE" (64-bit IEEE float)
           - int dtype     -> not supported
    """
    is_float = np.issubdtype(dtype, np.floating)

    if sample_width == 2:
        return "PCM_16"
    if sample_width == 3:
        return "PCM_24"
    if sample_width == 4:
        return "FLOAT" if is_float else "PCM_32"
    if sample_width == 8:
        if is_float:
            return "DOUBLE"
        raise NotImplementedError(
            "8-byte integer PCM is not supported. Use float64 for DOUBLE."
        )

    raise NotImplementedError(
        f"write_wav supports only sample_width in {2, 3, 4, 8}, got {sample_width}"
    )


def write_wav(info: WavInfo, data: np.ndarray) -> bytes:
    """
    Encode audio data back into a WAV file using soundfile.

    Assumes:
      - data.shape == (n_frames, n_channels)
      - info.sample_width in {2, 3, 4, 8}
      - data is numeric (float or int). For integer subtypes, float data
        will be clipped/quantized by soundfile.

    Behavior:
      - Chooses subtype based on info.sample_width and data.dtype:
          * 2 bytes:  PCM_16
          * 3 bytes:  PCM_24
          * 4 bytes:  FLOAT (if float) or PCM_32 (if int)
          * 8 bytes:  DOUBLE (float64 only)
      - frame_rate taken from info.frame_rate
      - n_channels must match info.n_channels
    """
    if data.ndim != 2:
        raise ValueError(
            f"data must be 2D (n_frames, n_channels), got shape={data.shape}"
        )

    n_frames, n_channels_actual = data.shape
    if n_channels_actual != info.n_channels:
        raise ValueError(
            f"data channels ({n_channels_actual}) do not match "
            f"info.n_channels ({info.n_channels})"
        )

    # Ensure we work with a concrete numpy dtype
    data = np.asarray(data)
    subtype = _choose_wav_subtype(info.sample_width, data.dtype)

    buf = io.BytesIO()
    # soundfile can write to file-like objects, including BytesIO
    sf.write(
        buf,
        data,
        info.frame_rate,
        format="WAV",
        subtype=subtype,
    )

    return buf.getvalue()
