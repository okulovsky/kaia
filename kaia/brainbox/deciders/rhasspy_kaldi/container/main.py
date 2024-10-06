import sys
import subprocess
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notebook', action='store_true')
    parser.add_argument('-r', '--rhasspy', action='store_true')
    parser.add_argument('-l', '--language')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0',"--NotebookApp.token=''"], cwd='/repo')
        exit(0)

    if args.rhasspy:
        subprocess.call(["bash","/usr/lib/rhasspy/bin/rhasspy-voltron",'--user-profiles', '/profiles', '--profile', args.language])
        exit(0)

    from utils import load_rhasspy_modules
    load_rhasspy_modules()
    from server import RhasspyKaldiServer
    RhasspyKaldiServer()()