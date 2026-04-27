import shutil
import time
import webbrowser

from avatar.daemon import SoundEvent
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from avatar.app import compile_frontend
from loguru import logger
from kaia.utils.wav_info import wav_check

if __name__ == '__main__':
    working_folder = Loc.data_folder/'demo'
    compile_frontend(working_folder / 'avatar' / 'frontend')

    settings = KaiaAppSettings()
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.custom_avatar_resources_folder = Loc.root_folder/'kaia/app/files/avatar-resources'
    app = settings.create_app(working_folder)
    app.get_fork_app(None).run()
    app.avatar_api.wait_for_connection(5 )
    webbrowser.open('http://127.0.0.1:13002')
    client = app.create_avatar_client()
    while True:
        time.sleep(1)
        if False:
            for message in client.pull(timeout_in_seconds=0):
                if isinstance(message, SoundEvent):
                    with open("sound.wav", 'wb') as f:
                        f.write(app.avatar_api.cache.read(message.file_id))
                        wav_check("sound.wav")


