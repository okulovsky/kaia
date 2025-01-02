import os

from kaia.kaia import KaiaServer, KaiaApi, KaiaServerSettings, Bus
from pathlib import Path
from kaia.common import Loc
from .app import KaiaApp

def set_web_service_and_api(app: KaiaApp):
    os.makedirs(app.folder/'kaia', exist_ok=True)
    cache_folder = app.folder/'kaia/cache'
    os.makedirs(cache_folder, exist_ok=True)
    settings = KaiaServerSettings(
        app.folder/'kaia'/'db',
        cache_folder,
        additional_static_folders=dict(additional = Path(__file__).parent/'files/gui'),
        custom_session_id=app.session_id
    )
    app.kaia_server = KaiaServer(settings)
    bus = Bus(settings.db_path)
    app.kaia_api = KaiaApi(bus, app.session_id, cache_folder=cache_folder)

