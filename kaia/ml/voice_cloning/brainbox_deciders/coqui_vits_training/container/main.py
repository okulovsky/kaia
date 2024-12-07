import sys
from yourtts_train import YourTTSTrain
from vits_train import VITSTrain
from vits_multispeaker_train import VITSMultispeakerTrain
from run_phonemizer import phonemize
import os
from pathlib import Path
import subprocess

if __name__ == '__main__':
    if len(sys.argv)<2:
        raise ValueError(f"Incorrect arguments {sys.argv}")

    if sys.argv[1] == 'yourtts':
        starter = YourTTSTrain(
            f'/data/{sys.argv[2]}',
            '/data/training',
            f'/data/{sys.argv[3]}'
        )
        starter.make_all()
    elif sys.argv[1] == 'vits':
        starter = VITSTrain(
            f'/data/{sys.argv[2]}',
            '/data/training',
            f'/data/{sys.argv[3]}'
        )
        starter.make_all()
    elif sys.argv[1] == 'vits-multispeaker':
        starter = VITSMultispeakerTrain(
            f'/data/{sys.argv[2]}',
            '/data/training',
            f'/data/{sys.argv[3]}'
        )
        starter.make_all()
    elif sys.argv[1] == 'notebook':
        subprocess.call(['jupyter', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0'], cwd='/repo')
    elif sys.argv[1] == 'phonemize':
        phonemize()
    else:
        raise ValueError(f"Incorrect arguments {sys.argv}")
