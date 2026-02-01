import subprocess
import argparse
import sys
from installation import install
import sys
sys.path.append('/home/app/repo/')
sys.path.append('/home/app/repo/third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import AutoModel
from server import CosyVoiceApp
import os
os.environ["MODELSCOPE_CACHE"] = "/resources/modelscope"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notebook', action='store_true')
    parser.add_argument('-i', '--install', action='store_true')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0', "--NotebookApp.token=''"], cwd='/repo')
        exit(0)

    if args.install:
        install()
        exit(0)

    cosyvoice = AutoModel(model_dir='/resources/pretrained_models/Fun-CosyVoice3-0.5B')
    CosyVoiceApp(cosyvoice).create_app().run('0.0.0.0',8080)







