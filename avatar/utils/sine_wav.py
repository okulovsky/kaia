import io
import wave
import struct
import math

def sine_wav(amplitude: int, duration_seconds: float = 2.0, sample_rate: int = 22050) -> bytes:
    n = int(sample_rate * duration_seconds)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack(f'<{n}h', *[
            int(amplitude * math.sin(2 * math.pi * 440 * i / sample_rate))
            for i in range(n)
        ]))
    return buf.getvalue()
