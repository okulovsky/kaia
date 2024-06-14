from typing import *
from pathlib import Path
from yo_fluq_ds import Query
import wavfile
import numpy as np
import pandas as pd
import wave, audioop
import shutil
import os

class VolumeNormalization:
    @staticmethod
    def compute_volumes(all_paths: Iterable[Path]):
        rows = []
        for path in all_paths:
            for file in Query.folder(path):
                [sample_rate, data] = wavfile.read(file, 'r')
                rows.append(dict(c=path, volume=np.abs(data).mean()))
        df = pd.DataFrame(rows)
        factors = (2000 / df.groupby('c').volume.mean()).to_dict()
        return factors

    @staticmethod
    def change_volume_file(input_file: Path, output_file: Path, factor: float):
        with wave.open(str(input_file), 'rb') as wav:
            p = wav.getparams()
            with wave.open(str(output_file), 'wb') as audio:
                audio.setparams(p)
                frames = wav.readframes(p.nframes)
                audio.writeframesraw(audioop.mul(frames, p.sampwidth, factor))


    @staticmethod
    def change_volumn_folder(input_folder: Path, output_folder: Path, factor: float):
        shutil.rmtree(output_folder, ignore_errors=True)
        os.makedirs(output_folder)
        for file in Query.folder(input_folder):
            VolumeNormalization.change_volume_file(file, output_folder / file.name, factor)


