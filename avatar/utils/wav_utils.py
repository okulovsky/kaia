import struct
from dataclasses import dataclass
import numpy as np


@dataclass
class AudioSegment:
    amplitude: float
    duration: float


def split_wav_by_amplitude(wav_bytes: bytes, block_size: int = 512) -> list[AudioSegment]:
    sample_rate, samples = _parse_pcm(wav_bytes)
    if len(samples) == 0:
        return []

    normalised = samples.astype(np.float32) / 32767.0
    n_blocks = len(normalised) // block_size
    if n_blocks == 0:
        amp = round(float(np.mean(np.abs(normalised))), 2)
        return [AudioSegment(amp, len(samples) / sample_rate)]

    block_amps = [
        float(np.mean(np.abs(normalised[i * block_size:(i + 1) * block_size])))
        for i in range(n_blocks)
    ]

    _CHANGE_RATIO = 0.3
    _CONFIRM_BLOCKS = 2

    def _changed(new_amp, ref_amp):
        return abs(new_amp - ref_amp) / max(ref_amp, 1e-4) > _CHANGE_RATIO

    segments: list[AudioSegment] = []
    seg_amps = [block_amps[0]]
    pending: list[float] = []

    for amp in block_amps[1:]:
        if not pending:
            if _changed(amp, float(np.mean(seg_amps))):
                pending = [amp]
            else:
                seg_amps.append(amp)
        else:
            pending_mean = float(np.mean(pending))
            if not _changed(amp, pending_mean):
                pending.append(amp)
                if len(pending) >= _CONFIRM_BLOCKS:
                    segments.append(AudioSegment(round(float(np.mean(seg_amps)), 2), len(seg_amps) * block_size / sample_rate))
                    seg_amps = pending
                    pending = []
            else:
                # Transition block didn't stabilise: absorb it into the current segment
                seg_amps.extend(pending)
                pending = []
                if _changed(amp, float(np.mean(seg_amps))):
                    pending = [amp]
                else:
                    seg_amps.append(amp)

    if pending:
        if len(pending) >= _CONFIRM_BLOCKS:
            segments.append(AudioSegment(round(float(np.mean(seg_amps)), 2), len(seg_amps) * block_size / sample_rate))
            seg_amps = pending
        else:
            seg_amps.extend(pending)

    segments.append(AudioSegment(round(float(np.mean(seg_amps)), 2), len(seg_amps) * block_size / sample_rate))
    return segments


def _parse_pcm(wav_bytes: bytes) -> tuple[int, np.ndarray]:
    """Parse 16-bit mono PCM from WAV bytes.  Ignores declared chunk sizes so
    it works with streaming WAV files that have placeholder 0 sizes."""
    i = 12  # skip 'RIFF' + 4-byte size + 'WAVE'
    sample_rate = 16000

    while i + 8 <= len(wav_bytes):
        chunk_id = wav_bytes[i:i + 4]
        chunk_size = struct.unpack_from('<I', wav_bytes, i + 4)[0]

        if chunk_id == b'fmt ':
            sample_rate = struct.unpack_from('<I', wav_bytes, i + 8 + 4)[0]
            i += 8 + chunk_size
        elif chunk_id == b'data':
            # Read everything from here to EOF as PCM, ignoring declared size
            pcm_bytes = wav_bytes[i + 8:]
            # Truncate to an even number of bytes (Int16 = 2 bytes per sample)
            pcm_bytes = pcm_bytes[:len(pcm_bytes) & ~1]
            samples = np.frombuffer(pcm_bytes, dtype=np.int16)
            return sample_rate, samples
        else:
            if chunk_size == 0 or chunk_size > len(wav_bytes):
                break
            i += 8 + chunk_size

    return sample_rate, np.array([], dtype=np.int16)
