import subprocess
from server import ZonosApp
import argparse
import sys
from pathlib import Path
from zonos_model import ZonosModel

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notebook', action='store_true')
    parser.add_argument('-i', '--install', action='store_true')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0', "--NotebookApp.token=''"], cwd='/repo')
        exit(0)

    m = ZonosModel()
    if args.install:
        m.train(Path(__file__).parent / "lina.mp3")
        exit(0)


    ZonosApp(m).create_app().run('0.0.0.0',8080)
