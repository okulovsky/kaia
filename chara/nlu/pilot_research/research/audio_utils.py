"""
Audio utilities for the whisper research pipeline.

Usage:
    python research/audio_utils.py research/to_zip/somefile.aac output.wav
    python research/audio_utils.py research/to_zip/somefile.aac   # plays via afplay (Mac)
    python research/audio_utils.py --convert-all                   # converts all → research/wav/
"""
import subprocess
import tempfile
import os
import sys
import numpy as np

WHISPER_SR = 16_000
WAV_OUT_DIR = 'research/wav'


def decode_for_whisper(path: str) -> np.ndarray:
    import soundfile as sf
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', path, '-ar', str(WHISPER_SR), '-ac', '1', '-f', 'wav', tmp_path],
            check=True, capture_output=True,
        )
        audio, _ = sf.read(tmp_path, dtype='float32')
        return audio
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_to_wav(src: str, dst: str, sample_rate: int | None = None) -> None:
    cmd = ['ffmpeg', '-y', '-i', src]
    if sample_rate is not None:
        cmd += ['-ar', str(sample_rate)]
    cmd += ['-ac', '1', dst]
    subprocess.run(cmd, check=True, capture_output=True)


def convert_all(src_dir: str = 'research/to_zip', out_dir: str = WAV_OUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(src_dir) if f.endswith('.aac'))
    print(f"Converting {len(files)} files → {out_dir}/")
    for i, fname in enumerate(files, 1):
        dst = os.path.join(out_dir, fname[:-4])
        if os.path.exists(dst):
            continue
        convert_to_wav(os.path.join(src_dir, fname), dst)
        if i % 100 == 0 or i == len(files):
            print(f"  {i}/{len(files)}")
    print(f"Done. WAV files in: {os.path.abspath(out_dir)}/")


if __name__ == '__main__':
    if '--convert-all' in sys.argv:
        convert_all()
        sys.exit(0)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    if len(sys.argv) >= 3:
        dst = sys.argv[2]
        convert_to_wav(src, dst)
        print(f"Saved: {dst}")
    else:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            dst = tmp.name
        try:
            convert_to_wav(src, dst)
            subprocess.run(['afplay', dst])
        finally:
            os.unlink(dst)
