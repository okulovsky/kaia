import os
import subprocess
import sys

from brainbox.framework import Loc, FileIO
import shutil
from pathlib import Path
from brainbox.release.documentation_handler import create_documentation


TOX_FILE = '''
[tox]
envlist = py310, py311, py312, py313
isolated_build = True

[testenv]
changedir = brainbox/tests
commands =
    python -m unittest discover -s . -p "test_*.py"
'''

if __name__ == '__main__':
    folder = Loc.temp_folder/'brainbox_release_tox'
    shutil.rmtree(folder, ignore_errors=True)

    src_root = Path(__file__).parent.parent
    shutil.copytree(src_root, folder/'brainbox')
    shutil.copy(Path(__file__).parent/'pyproject.toml', folder)

    documentation = create_documentation()
    FileIO.write_text(documentation, folder/'README.md')
    with open(folder/'tox.ini', 'w') as stream:
        stream.write(TOX_FILE)

    subprocess.call([sys.executable,'-m','tox','-rvv'], cwd=folder, env={**os.environ, "PYTHONPATH": ""})



