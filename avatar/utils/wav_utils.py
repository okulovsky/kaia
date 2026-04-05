import struct
import numpy as np


def split_wav_by_amplitude(
    wav_bytes: bytes,
    block_size: int = 512,
    silence_threshold: float = 0.01,
) -> list[float]:
    """
    Split WAV audio into contiguous segments of silence / non-silence and return
    the mean normalised amplitude of each segment.

    Tolerant of streaming WAV files where RIFF/data chunk sizes are 0 or
    placeholder values — the data chunk is read until end-of-file regardless of
    the declared size.

    Args:
        wav_bytes:         Raw bytes of a WAV file.
        block_size:        Number of samples per analysis block.
        silence_threshold: Normalised amplitude below which a block is silence.

    Returns:
        List of mean normalised amplitudes, one entry per contiguous segment
        (silence and non-silence segments both appear).
    """
    _, samples = _parse_pcm(wav_bytes)
    if len(samples) == 0:
        return []

    normalised = samples.astype(np.float32) / 32767.0

    # Compute per-block mean absolute amplitude
    n_blocks = len(normalised) // block_size
    if n_blocks == 0:
        return [float(np.mean(np.abs(normalised)))]

    block_amps = [
        float(np.mean(np.abs(normalised[i * block_size:(i + 1) * block_size])))
        for i in range(n_blocks)
    ]

    # Group consecutive blocks with the same silence/non-silence status
    segments: list[float] = []
    current: list[float] = [block_amps[0]]
    current_silent = block_amps[0] < silence_threshold

    for amp in block_amps[1:]:
        is_silent = amp < silence_threshold
        if is_silent == current_silent:
            current.append(amp)
        else:
            segments.append(float(np.mean(current)))
            current = [amp]
            current_silent = is_silent

    segments.append(float(np.mean(current)))
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
