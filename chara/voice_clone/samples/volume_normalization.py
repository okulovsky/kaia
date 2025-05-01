import os
import wave
import numpy as np
from pathlib import Path
import audioop

def change_volume(input_file: Path, output_file: Path, factor: float):
    with wave.open(str(input_file), 'rb') as wav:
        p = wav.getparams()
        os.makedirs(Path(output_file).parent, exist_ok=True)
        with wave.open(str(output_file), 'wb') as audio:
            audio.setparams(p)
            frames = wav.readframes(p.nframes)
            audio.writeframesraw(audioop.mul(frames, p.sampwidth, factor))

