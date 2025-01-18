from brainbox.framework import BrainBoxServer, ControllerRegistry, BrainBoxServiceSettings, Locator
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--data-folder', required=True)
parser.add_argument('-p', '--port', default='8090')

if __name__ == '__main__':
    args = parser.parse_args()
    locator = Locator(Path(args.data_folder))
    registry = ControllerRegistry.discover()
    registry.locator = locator
    settings = BrainBoxServiceSettings(
        registry=registry,
        locator=locator,
        port=int(args.port)
    )
    server = BrainBoxServer(settings)
    server()
