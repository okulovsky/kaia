from avatar.app import compile_frontend
from kaia.app import KaiaAppSettings, KaiaApp
from pathlib import Path
from brainbox import BrainBox
from loguru import logger
import argparse
import time

def start_kaia(settings: KaiaAppSettings):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--data-folder', required=True)
    parser.add_argument('-p', '--port', default='13002')

    args = parser.parse_args()
    port = int(args.port)
    data_folder = Path(args.data_folder)

    logger.info(f"Running kaia at the port {port} in the folder {data_folder}")
    settings.brainbox = None
    settings.avatar_server.port = port

    app = KaiaApp(data_folder)
    app.brainbox_api = BrainBox.Api("http://127.0.0.1:8090")
    app.brainbox_cache_folder = data_folder / 'brainbox/cache'
    settings.bind_app(app)

    if app.avatar_server is not None:
        frontend_folder = app.avatar_server.settings.frontend_folder
        if frontend_folder is not None:
            compile_frontend(frontend_folder)

    settings.brainbox_setup.execute(app.brainbox_api)

    app.get_fork_app(None).run()

    while True:
        time.sleep(1)

