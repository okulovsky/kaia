from server import CoquiInferenceWebApp
from tts_loader import load_tts
import sys
import subprocess
from pathlib import Path
import argparse

def install(model_name, mode):
    print(f"Installing model {model_name} in mode {mode}")
    if mode == 'simple':
        data = load_tts(model_name)
        print(f"Successfully loaded")
        return
    ret_code = subprocess.run(
        [
            sys.executable,
            Path(__file__).parent/'installer_script.py',
            model_name
        ],
        input='y'.encode('ascii'),
    )
    print(f'Installation script returned code {ret_code}')





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--notebook', action='store_true')
    parser.add_argument('-i','--install')
    parser.add_argument('-m','--install-mode')
    parser.add_argument('-a','--autoload')


    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0'], cwd='/repo')
        exit(0)

    if args.install is not None or args.install_mode is not None:
        if args.install is None or args.install_mode is None:
            raise ValueError("`install` and `install-mode` must be set together")
        install(args.install, args.install_mode)
        exit(0)

    factory = CoquiInferenceWebApp(args.autoload)
    factory.create_app().run('0.0.0.0', 8084)
