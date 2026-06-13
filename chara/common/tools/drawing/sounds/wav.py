from yo_fluq import FileIO
from .wav_wrap import WavWrap
from .wav_list import WavList
from brainbox import File
from pathlib import Path
from typing import Iterable
from foundation_kaia.misc import Loc
import subprocess
from copy import copy

def _make_wav(wav) -> WavWrap:
    if isinstance(wav, str) or isinstance(wav, Path):
        path = Path(wav)
        if path.is_file():
            return WavWrap(path.name, None, path)
        else:
            raise ValueError(f"{path} is not a file")
    elif isinstance(wav, File):
        return WavWrap(wav.name, wav.content, None)
    elif isinstance(wav, bytes) or isinstance(wav, bytearray):
        return WavWrap(None, wav, None)
    elif isinstance(wav, WavWrap):
        return copy(wav)
    else:
        raise TypeError(f"Unexpected type {type(wav)}")



class WavClass:
    def __init__(self):
        self.List = WavList
        self.Wrap = WavWrap

    def __call__(self, wav):
        try:
            if isinstance(wav, str) or isinstance(wav,Path):
                path = Path(wav)
                if path.is_dir():
                    return WavList([_make_wav(file) for file in path.iterdir()])
                else:
                    return _make_wav(path)
            elif isinstance(wav, tuple) or isinstance(wav, list):
                return WavList([_make_wav(w) for w in wav])
            elif isinstance(wav, WavList):
                return WavList([_make_wav(w) for w in wav.wavs])
            else:
                return _make_wav(wav)
        except Exception as e:
            raise ValueError(f"Cannot open wav file from {str(wav)[:1000]}") from e

    def one(self, wav) -> WavWrap:
        return _make_wav(wav)

    def many(self, wav) -> WavList:
        result = self(wav)
        if isinstance(result, WavWrap):
            return WavList([result])
        return result

    def concat_with_ffmpeg(self, paths: Iterable[Path], output_path: Path, keep_temp_file: bool = False):
        paths_list = list(paths)
        inputs = []
        for p in paths_list:
            inputs.extend(['-i', str(p)])
        n = len(paths_list)
        filter_complex = ''.join(f'[{i}:a]' for i in range(n)) + f'concat=n={n}:v=0:a=1[out]'
        args = ['ffmpeg'] + inputs + ['-filter_complex', filter_complex, '-map', '[out]', '-y', str(output_path)]
        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}. Output\n{err.output}')



Wav = WavClass()