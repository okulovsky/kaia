from chara.common.tools import Wav
from pathlib import Path


def compute_length(path: Path):
    files = list(sorted(path.glob("*.wav")))
    total = 0
    with open(path/'lengths', 'w') as f:
        for file in files:
            length = Wav(file).to_editable().duration_sec
            f.write(f"{file.name}: {length} sec\n")
            total += length
        f.write(f"\n\nTOTAL: {total} sec\n")

