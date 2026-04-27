import struct
import wave
import io
import numpy as np
from .common import message_handler, AvatarService, SoundEvent, SoundStreamingEndEvent
from pathlib import Path


def _fix_wav_header(data: bytes) -> bytes:
    data = bytearray(data)
    data_size = len(data) - 44
    struct.pack_into('<I', data, 4, 36 + data_size)   # RIFF chunk size
    struct.pack_into('<I', data, 40, data_size)        # data chunk size
    return bytes(data)


def _resample_wav(data: bytes, target_rate: int) -> bytes:
    with wave.open(io.BytesIO(data)) as r:
        n_channels = r.getnchannels()
        sample_width = r.getsampwidth()
        src_rate = r.getframerate()
        frames = r.readframes(r.getnframes())

    if src_rate == target_rate:
        return data

    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sample_width]
    samples = np.frombuffer(frames, dtype=dtype).astype(np.float64)
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels)

    ratio = target_rate / src_rate
    n_out = int(len(samples) * ratio)
    x_old = np.linspace(0, 1, len(samples))
    x_new = np.linspace(0, 1, n_out)
    if n_channels > 1:
        resampled = np.column_stack([np.interp(x_new, x_old, samples[:, c]) for c in range(n_channels)])
    else:
        resampled = np.interp(x_new, x_old, samples)

    resampled = np.clip(resampled, np.iinfo(dtype).min, np.iinfo(dtype).max).astype(dtype)

    buf = io.BytesIO()
    with wave.open(buf, 'w') as w:
        w.setnchannels(n_channels)
        w.setsampwidth(sample_width)
        w.setframerate(target_rate)
        w.writeframes(resampled.tobytes())
    return buf.getvalue()


class UploadedWavFixer(AvatarService):
    def __init__(self, cache_folder: Path | None = None, resample_to_rate: int | None = None):
        self.cache_folder = cache_folder
        self.resample_to_rate = resample_to_rate

    @message_handler
    def on_streaming_end(self, event: SoundStreamingEndEvent) -> SoundEvent | None:
        if not event.success:
            return None
        path = self.cache_folder / event.file_id
        fixed = _fix_wav_header(path.read_bytes())
        if self.resample_to_rate is not None:
            fixed = _resample_wav(fixed, self.resample_to_rate)
        path.write_bytes(fixed)
        return SoundEvent(event.file_id)

    def requires_brainbox(self):
        return False
