from server import CoquiInferenceWebApp
from tts_loader import load_tts
import sys
import subprocess
from pathlib import Path

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
    print(f"Running with arguments\n{sys.argv}")

    if len(sys.argv) == 1:
        print("Running web-server")
        factory = CoquiInferenceWebApp()
        factory.create_app().run('0.0.0.0', 8084)
        exit(0)

    if len(sys.argv) == 3:
        install(sys.argv[1], sys.argv[2])
        exit(0)

    if len(sys.argv) == 2:
        if sys.argv[1] == 'notebook':
            subprocess.call(['jupyter','notebook','--allow-root','--port','8899', '--ip', '0.0.0.0'], cwd='/repo')
            exit(0)
        else:
            raise ValueError('If one argument is provided, it should be `notebook`')
    else:
        raise ValueError(f'Unexpected arguments: {sys.argv}')
