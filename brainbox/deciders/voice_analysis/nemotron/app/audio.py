import struct
import numpy as np


class PcmStreamDecoder:
    """Turns arbitrarily chunked bytes (a WAV stream or raw mono PCM16LE) into float32 mono samples."""

    def __init__(self, default_sample_rate: int = 16000):
        self.sample_rate = default_sample_rate
        self._channels = 1
        self._buffer = b''
        self._header_done = False
        self._leftover = b''

    def feed(self, data: bytes) -> np.ndarray | None:
        if not self._header_done:
            self._buffer += data
            if len(self._buffer) < 4:
                return None
            if self._buffer[:4] != b'RIFF':
                data, self._buffer = self._buffer, b''
                self._header_done = True
            else:
                data = self._parse_wav_header()
                if data is None:
                    return None
        return self._decode(data)

    def _parse_wav_header(self) -> bytes | None:
        buf = self._buffer
        if len(buf) < 12:
            return None
        pos = 12
        while True:
            if len(buf) < pos + 8:
                return None
            chunk_id, size = struct.unpack_from('<4sI', buf, pos)
            if chunk_id == b'data':
                self._header_done = True
                self._buffer = b''
                return buf[pos + 8:]
            if len(buf) < pos + 8 + size:
                return None
            if chunk_id == b'fmt ':
                tag, channels, rate, _, _, bits = struct.unpack_from('<HHIIHH', buf, pos + 8)
                if tag not in (1, 0xFFFE) or bits != 16:
                    raise ValueError("Only 16-bit PCM WAV is supported")
                self._channels = channels
                self.sample_rate = rate
            pos += 8 + size + (size & 1)

    def _decode(self, data: bytes) -> np.ndarray | None:
        data = self._leftover + data
        frame = 2 * self._channels
        usable = len(data) - len(data) % frame
        self._leftover = data[usable:]
        if usable == 0:
            return None
        samples = np.frombuffer(data[:usable], dtype='<i2').astype(np.float32) / 32768.0
        if self._channels > 1:
            samples = samples.reshape(-1, self._channels).mean(axis=1)
        return samples


def decode_all(data: bytes, default_sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    decoder = PcmStreamDecoder(default_sample_rate)
    samples = decoder.feed(data)
    if samples is None:
        raise ValueError("No audio data")
    return samples, decoder.sample_rate
