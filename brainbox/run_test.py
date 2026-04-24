from brainbox import BrainBox
import argparse
from foundation_kaia.releasing.mddoc import run_doc_files
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', default='8090')
parser.add_argument('-o', '--host', default='127.0.0.1')

if __name__ == '__main__':
    args = parser.parse_args()
    api = BrainBox.Api(f'http://{args.host}:{args.port}')
    api.wait_for_connection(1)
    run_doc_files(Path(__file__).parent.parent/'doc')
