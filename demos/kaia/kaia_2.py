import os

from kaia.kaia.server_2 import KaiaApi, KaiaServer, KaiaServerSettings, Bus
from pathlib import Path
from kaia.infra import Loc


PORT = 18890

def create_kaia_2_service_and_api(session_id: str, folder: str = 'demo/kaia'):
    db_path = Loc.data_folder/folder/'db'
    os.unlink(db_path)
    cache_folder = Loc.data_folder/folder/'file_cache'
    os.makedirs(cache_folder, exist_ok=True)
    server = KaiaServer(KaiaServerSettings(
        db_path,
        cache_folder,
        additional_static_folders={'additional': Path(__file__).parent/'files/gui'},
        port = PORT,
        custom_session_id=session_id,
    ))
    bus = Bus(db_path)
    api = KaiaApi(bus, session_id, None, cache_folder)
    return server, api