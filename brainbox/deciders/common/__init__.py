from unittest import TestCase
from ...framework import Loc, FileIO, LocalExecutor
from pathlib import Path

def check_if_its_sound(content, tc: TestCase):
    import soundfile as sf
    with Loc.create_test_file() as tmp_filename:
        FileIO.write_bytes(content, tmp_filename)
        f = sf.SoundFile(tmp_filename)
        duration = f.frames / f.samplerate
        tc.assertGreater(duration, 1)
    f.close()


VOICEOVER_TEXT = 'The quick brown fox jumps over the lazy dog'

def download_file(url: str, file: Path|str):
    LocalExecutor().execute(['curl', '-L', url, '--output', str(file)])