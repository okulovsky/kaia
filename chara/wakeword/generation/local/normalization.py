import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def normalize(source, destination, sample_rate=16000):
    if sample_rate != 16000:
        raise ValueError("wakeword audio must be 16 kHz")
    data, rate = sf.read(source, dtype="float32", always_2d=True)
    if not len(data) or not np.isfinite(data).all():
        raise ValueError("empty or nonfinite audio")
    data = data.mean(axis=1)
    if rate != sample_rate:
        divisor = math.gcd(rate, sample_rate)
        data = resample_poly(data, sample_rate // divisor, rate // divisor)
    if not np.isfinite(data).all():
        raise ValueError("normalization produced nonfinite audio")
    sf.write(destination, np.clip(data, -1, 1), sample_rate, subtype="PCM_16")
    return Path(destination)
