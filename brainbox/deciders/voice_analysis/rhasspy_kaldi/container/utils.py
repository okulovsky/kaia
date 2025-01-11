from pathlib import Path
import sys
from dataclasses import dataclass

train_path = Path('/models')
rhasspy_path = Path('/profiles')
profile_path = Path('/usr/lib/rhasspy/rhasspy-profile/rhasspyprofile/profiles/')
kaldi_path = Path('/usr/lib/rhasspy/.venv/lib/kaldi/')


def load_rhasspy_modules():
    dir_file = Path('/usr/lib/rhasspy/RHASSPY_DIRS')
    dirs = []
    with open(dir_file, 'r') as file:
        while True:
            d = file.readline().strip()
            if d == '':
                break
            dirs.append(d)

    for d in dirs:
        sys.path.append(str(dir_file.parent / d))

