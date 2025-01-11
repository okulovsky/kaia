import os
import sys
import subprocess
from pathlib import Path
import argparse
import shutil

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--fix', action='store_true')
    parser.add_argument('-i','--install')
    parser.add_argument('-c','--commit')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.fix:
        fix_path = Path('/home/app/fix')
        comfy_path = Path('/home/app/ComfyUI')
        for folder_name in ['models', 'input']:
            for item in os.listdir(f'/home/app/fix/{folder_name}'):
                src = fix_path/folder_name/item
                dst = Path()/folder_name/item
                if not dst.is_file() and not dst.is_dir():
                    if src.is_dir():
                        shutil.copytree(src, dst)
                    elif src.is_file():
                        os.makedirs(dst.parent, exist_ok=True)
                        shutil.copy(src, dst)
        exit(0)

    if args.install:
        subprocess.call(
            ['git', 'clone', args.install],
            cwd='/home/app/ComfyUI/custom_nodes'
        )
        if args.commit is not None:
            subprocess.call(
                ['git','reset','--hard', args.commit]
            )
        exit(0)

    subprocess.run([sys.executable, '/home/app/ComfyUI/main.py', '--listen'])

