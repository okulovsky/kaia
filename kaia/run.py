import time
import webbrowser
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from avatar.app import compile_frontend
from brainbox.framework import BrainBoxSetup
from brainbox.deciders import RhasspyKaldi, Piper, Resemblyzer, Whisper


if __name__ == '__main__':
    working_folder = Loc.data_folder/'demo'
    compile_frontend(working_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    app = settings.create_app(working_folder)
    app.get_fork_app(None).run()
    app.avatar_api.wait_for_connection(5)

    settings.brainbox_setup.execute(app.brainbox_api)

    webbrowser.open('http://127.0.0.1:13002')
    while True:
        time.sleep(1)
