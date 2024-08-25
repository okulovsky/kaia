import sys
import subprocess
from server import ResemblyzerServer
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notebook', action='store_true')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        subprocess.call(['jupyter', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0'], cwd='/repo')
        exit(0)

    ResemblyzerServer()()
