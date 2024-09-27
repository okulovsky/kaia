import time

from kaia.kaia.server.server import KaiaServer, KaiaServerSettings
from kaia.kaia.server.api import KaiaApi, Message
from kaia.kaia.server.bus import Bus, BusItem
from kaia.infra import Loc
from kaia.infra.app import KaiaApp
from pathlib import Path

if __name__ == '__main__':
    with Loc.create_temp_file('kaia-server-tests','db') as fname:
        settings = KaiaServerSettings(
            db_path = fname,
            file_cache_folder = Path(__file__).parent/'test_1/files/cache',
            additional_static_folders = dict(alt=Path(__file__).parent/'test_1/files/alternative_static')
        )
        with KaiaApi.Test(settings) as api:
            api.add_message(Message(Message.Type.ToUser, "Hey!"))
            api.add_message(Message(Message.Type.FromUser, "Hello!", avatar='/alt/lina.png'))
            api.add_image('img1.png')
            api.add_sound('sound1.mpeg')
            #api.add_sound('sound2.mpeg')
            time.sleep(60*60)
