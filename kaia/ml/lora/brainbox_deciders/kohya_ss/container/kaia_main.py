import subprocess
import argparse
import json
import sys
import time
from pathlib import Path

import toml

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g','--gradio', action='store_true')
    parser.add_argument('-t','--train')
    parser.add_argument('-m','--mock', action='store_true')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.gradio:
        subprocess.call(["python3", "kohya_gui.py", "--listen", "0.0.0.0", "--server_port", "7860", "--headless"])
        exit(0)

    if args.train is not None:
        path = Path('/app/training/'+args.train)
        with open(path/'parameters.json') as file:
            params = json.load(file)
        if not args.mock:
            error_code = subprocess.call(params)
            with open(path/'error_code.txt', 'w') as error_code_file:
                error_code_file.write(str(error_code))
        else:
            with open(path/'model/config.toml') as cfg_file:
                cfg = toml.load(cfg_file)
            output_path = Path(cfg['output_dir'])
            output_path/=cfg['output_name']+'.mock.safetensors'
            with open(output_path,'wb') as file:
                file.write(b'koyha_ss_mock_output_file')

            for i in range(100):
                print(f'steps: {i}%', file=sys.stderr)
                time.sleep(0.1)

            with open(path/'error_code.txt', 'w') as error_code_file:
                error_code_file.write("0")












