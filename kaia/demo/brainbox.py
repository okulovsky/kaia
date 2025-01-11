import os

from brainbox.framework import (
    BrainBoxServer, AlwaysOnPlanner, BrainBoxApi,BrainBoxServiceSettings, Locator, ControllerRegistry
)
from .app import KaiaApp

def set_brainbox_service_and_api(app: KaiaApp):
    os.makedirs(app.folder/'brainbox', exist_ok=True)
    registry = ControllerRegistry.discover()
    locator = Locator(app.folder/'brainbox')
    settings = BrainBoxServiceSettings(
        registry,
        AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart),
        locator=locator,
        stop_controllers_at_termination=False
    )
    app.brainbox_server = BrainBoxServer(settings)
    app.brainbox_api = BrainBoxApi(f'127.0.0.1:{settings.port}')
    app.brainbox_cache_folder = locator.cache_folder


