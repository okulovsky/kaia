import wave
import numpy as np
from scipy.fft import rfft, rfftfreq
from collections import deque
from dataclasses import dataclass
from io import BytesIO

@dataclass
class Segment:
    duration: float  # seconds
    amplitude: float  # RMS amplitude
    frequency: float | None  # Hz, or None if silence

    @staticmethod
    def analyze_wav(content: bytes, window_ms: int = 100, silence_threshold: float = 0.01) -> list['Segment']:
        stream = BytesIO(content)
        with wave.open(stream, 'rb') as wf:
            framerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            audio = wf.readframes(n_frames)

        dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sampwidth]
        samples = np.frombuffer(audio, dtype=dtype).astype(np.float32)

        # Mono only
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        samples /= np.abs(samples).max()  # Normalize

        window_size = int(framerate * window_ms / 1000)
        num_windows = len(samples) // window_size

        segments = []

        for i in range(num_windows):
            window = samples[i * window_size: (i + 1) * window_size]
            amplitude = np.sqrt(np.mean(window ** 2))

            if amplitude < silence_threshold:
                segments.append(Segment(duration=window_size / framerate, amplitude=0.0, frequency=None))
            else:
                # Find dominant frequency
                spectrum = np.abs(rfft(window))
                freqs = rfftfreq(len(window), 1 / framerate)
                dominant_freq = freqs[np.argmax(spectrum)]
                segments.append(Segment(duration=window_size / framerate, amplitude=amplitude, frequency=dominant_freq))

        # Optional: merge consecutive identical segments
        merged: list[Segment] = []
        for seg in segments:
            if merged and seg.frequency == merged[-1].frequency and abs(seg.amplitude - merged[-1].amplitude) < 1e-3:
                merged[-1].duration += seg.duration
            else:
                merged.append(seg)

        return merged
