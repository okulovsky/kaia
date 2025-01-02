from brainbox.doc import run_all
from brainbox import BrainBox
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', default='8090')
parser.add_argument('-o', '--host', default='127.0.0.1')

if __name__ == '__main__':
    args = parser.parse_args()
    api = BrainBox.Api(f'{args.host}:{args.port}')
    api.wait(1)
    run_all(api)