import wave
import os
from pathlib import Path
import numpy as np
import audioop
from ...tools.wav_processor import WavProcessor


def _get_avg_volume(filepath):
    with wave.open(str(filepath), 'rb') as wav_file:
        samp_width = wav_file.getsampwidth()
        n_frames = wav_file.getnframes()
        frames = wav_file.readframes(n_frames)
        rms = audioop.rms(frames, samp_width)
        db = 20 * np.log10(rms) if rms > 0 else -np.inf  # Avoid log(0)
        return db


def build_statistics(folder: Path):
    folder = Path(folder)
    rows = []
    for character in os.listdir(folder):
        if not (folder/character).is_dir():
            continue
        for file in os.listdir(folder/character):
            path = str(folder/character/file)
            length = WavProcessor(path).get_length()
            volume = _get_avg_volume(path)
            rows.append(dict(
                path = path,
                character=character,
                file=file,
                length=length,
                volume=volume
            ))
    return rows
