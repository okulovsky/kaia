import wave
import io
import numpy as np
from pathlib import Path


class WavProcessor:
    def __init__(self, wav_file: Path|bytes|str, load_content: bool = True):
        if isinstance(wav_file, bytes):
            wav = io.BytesIO(wav_file)
        else:
            wav = str(wav_file)

        with wave.open(wav, 'rb') as wav_in:
            self.params = wav_in.getparams()
            self.framerate = wav_in.getframerate()
            self.n_channels = wav_in.getnchannels()
            self.sampwidth = wav_in.getsampwidth()
            self.total_frames = wav_in.getnframes()
            if load_content:
                self.frames = self._frames_to_array(wav_in.readframes(self.total_frames - 0))

    def _frames_to_array(self, frames):
        """Convert byte frames to a NumPy array of sample values."""
        dtype_map = {1: np.int8, 2: np.int16, 3: np.int32, 4: np.int32}
        dtype = dtype_map.get(self.sampwidth, np.int16)  # Default to int16

        # Convert bytes to NumPy array
        audio_array = np.frombuffer(frames, dtype=dtype)

        # Reshape for multi-channel audio
        audio_array = audio_array.reshape(-1, self.n_channels)

        return audio_array

    def cut(self, start_time, end_time):
        start_frame = int(start_time * self.framerate)
        end_frame = int(end_time * self.framerate)
        return self.frames[start_frame: end_frame]

    def frames_to_wav_bytes(self, frames):
        # Create in-memory WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_out:
            wav_out.setnchannels(self.n_channels)
            wav_out.setsampwidth(self.sampwidth)
            wav_out.setframerate(self.framerate)
            wav_out.writeframes(frames.astype(np.int16).tobytes())

        return wav_buffer.getbuffer()

    def create_silence(self, duration_seconds):
        num_frames = int(duration_seconds * self.framerate)

        # Create a silent NumPy array (zeroes)
        silent_audio = np.zeros((num_frames, self.n_channels), dtype=np.int16)

        return silent_audio

    def get_length(self):
        return self.total_frames / float(self.framerate)

    def fade(self, array, k_start=0.0, k_end=1.0):
        fade_array = np.linspace(k_start, k_end, array.shape[0])
        return (array * fade_array[:, np.newaxis]).astype(int)


