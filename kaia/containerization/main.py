import argparse
from pathlib import Path
from avatar.app import compile_frontend
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--data-folder', required=True)
parser.add_argument('-p', '--port', default='8090')

if __name__ == '__main__':
    args = parser.parse_args()
    port = int(args.port)
    data_folder = Path(args.data_folder)
    print(f"Running kaia at the port {port} in the folder {data_folder}")

    compile_frontend(data_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.custom_avatar_resources_folder = Loc.root_folder / 'kaia/app/files/avatar-resources'
    app = settings.create_app(data_folder)
    app.brainbox_server = None
    app.get_fork_app().run()
