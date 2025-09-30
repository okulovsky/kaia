import time
import webbrowser

from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from pathlib import Path

if __name__ == '__main__':
    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    app = settings.create_app(Loc.data_folder/'demo')
    app.get_fork_app(None).run()
    app.avatar_api.wait()
    webbrowser.open('http://127.0.0.1:13002/main')
    while True:
        time.sleep(1)
