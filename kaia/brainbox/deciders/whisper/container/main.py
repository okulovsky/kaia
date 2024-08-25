import sys
import subprocess
from server import WhisperApp
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Small web server around Whisper model"
    )
    parser.add_argument('-n', '--notebook', action='store_true')
    parser.add_argument('-a', '--autoload')

    args = parser.parse_args()
    print(f'Running with arguments {args}')

    if args.notebook:
        subprocess.call(['jupyter', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0'], cwd='/repo')
        exit(0)

    factory = WhisperApp(args.autoload)
    factory.create_app().run('0.0.0.0', 8084)

