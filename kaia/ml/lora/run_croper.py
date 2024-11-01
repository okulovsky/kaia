import os
from kaia.ml.lora.croper import run_croper
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) == 2:
        run_croper(Path(sys.argv[1]))
