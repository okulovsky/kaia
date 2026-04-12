from avatar.app import compile_frontend
from kaia.app import KaiaAppSettings, KaiaApp
from pathlib import Path
from brainbox import BrainBox
import argparse



def start_kaia(settings: KaiaAppSettings):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--data-folder', required=True)
    parser.add_argument('-p', '--port', default='13002')

    args = parser.parse_args()
    port = int(args.port)
    data_folder = Path(args.data_folder)
    print(f"Running kaia at the port {port} in the folder {data_folder}")

    compile_frontend(data_folder / 'avatar' / 'frontend')
    settings.brainbox = None
    settings.avatar_server.port = port

    app = KaiaApp(data_folder)
    app.brainbox_api = BrainBox.Api("http://127.0.0.1:8090")
    app.brainbox_cache_folder = data_folder/'brainbox/cache'
    settings.bind_app(app)
    app.get_fork_app().run()
