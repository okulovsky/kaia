from hashlib import sha256
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import soundfile as sf
import soxr
import torch

from piper_train.vits.mel_processing import spectrogram_torch

from .trim import trim_silence
from .vad import SileroVoiceActivityDetector

_DIR = Path(__file__).parent


def make_silence_detector() -> SileroVoiceActivityDetector:
    silence_model = _DIR / "models" / "silero_vad.onnx"
    return SileroVoiceActivityDetector(silence_model)


def cache_norm_audio(
    audio_path: Union[str, Path],
    cache_dir: Union[str, Path],
    detector: SileroVoiceActivityDetector,
    sample_rate: int,
    silence_threshold: float = 0.2,
    silence_samples_per_chunk: int = 480,
    silence_keep_chunks_before: int = 2,
    silence_keep_chunks_after: int = 2,
    filter_length: int = 1024,
    window_length: int = 1024,
    hop_length: int = 256,
    ignore_cache: bool = False,
) -> Tuple[Path, Path]:
    audio_path = Path(audio_path).absolute()
    cache_dir = Path(cache_dir)

    # Cache id is the SHA256 of the full audio path
    audio_cache_id = sha256(str(audio_path).encode()).hexdigest()

    audio_norm_path = cache_dir / f"{audio_cache_id}.pt"
    audio_spec_path = cache_dir / f"{audio_cache_id}.spec.pt"

    # Normalize audio
    audio_norm_tensor: Optional[torch.FloatTensor] = None
    if ignore_cache or (not audio_norm_path.exists()):
        # Trim silence first.
        #
        # The VAD model works on 16khz, so we determine the portion of audio
        # to keep and then reload just that portion.
        vad_sample_rate = 16000
        audio_raw, raw_sr = sf.read(audio_path, dtype="float32")
        if audio_raw.ndim > 1:
            audio_raw = np.mean(audio_raw, axis=1)
        audio_16khz = soxr.resample(audio_raw, raw_sr, vad_sample_rate)

        offset_sec, duration_sec = trim_silence(
            audio_16khz,
            detector,
            threshold=silence_threshold,
            samples_per_chunk=silence_samples_per_chunk,
            sample_rate=vad_sample_rate,
            keep_chunks_before=silence_keep_chunks_before,
            keep_chunks_after=silence_keep_chunks_after,
        )

        # Reload with offset/duration at the target sample rate
        start_sample = int(offset_sec * raw_sr)
        num_samples = int(duration_sec * raw_sr) if duration_sec else -1
        audio_segment, _ = sf.read(
            audio_path, start=start_sample, stop=start_sample + num_samples if num_samples > 0 else None, dtype="float32"
        )
        if audio_segment.ndim > 1:
            audio_segment = np.mean(audio_segment, axis=1)
        audio_norm_array = soxr.resample(audio_segment, raw_sr, sample_rate)

        # Save to cache directory
        audio_norm_tensor = torch.FloatTensor(audio_norm_array).unsqueeze(0)
        torch.save(audio_norm_tensor, audio_norm_path)

    # Compute spectrogram
    if ignore_cache or (not audio_spec_path.exists()):
        if audio_norm_tensor is None:
            # Load pre-cached normalized audio
            audio_norm_tensor = torch.load(audio_norm_path)

        audio_spec_tensor = spectrogram_torch(
            y=audio_norm_tensor,
            n_fft=filter_length,
            sampling_rate=sample_rate,
            hop_size=hop_length,
            win_size=window_length,
            center=False,
        ).squeeze(0)
        torch.save(audio_spec_tensor, audio_spec_path)

    return audio_norm_path, audio_spec_path
