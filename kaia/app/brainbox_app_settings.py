from dataclasses import dataclass
from .app import KaiaApp, IAppInitializer
from brainbox.framework import BrainBoxServer, BrainBoxServerSettings, ControllerRegistry, AlwaysOnPlanner, BrainBoxApi, \
    BrainBoxLocations
import os

@dataclass
class BrainboxAppSettings(IAppInitializer):
    default_resources_folder: bool = True

    def bind_app(self, app: 'KaiaApp'):
        brainbox_folder = app.working_folder / 'brainbox'
        os.makedirs(brainbox_folder, exist_ok=True)
        resources_folder = None
        if not self.default_resources_folder:
            resources_folder = brainbox_folder / 'resources'
            os.makedirs(resources_folder, exist_ok=True)

        registry = ControllerRegistry.discover(resources_folder)
        locations = BrainBoxLocations.default(brainbox_folder)
        settings = BrainBoxServerSettings(
            registry=registry,
            planner=AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart),
            locations = locations,
            stop_controllers_at_termination=False,
            port=8090,
        )
        app.brainbox_server = BrainBoxServer(settings)
        app.brainbox_api = BrainBoxApi(f'http://127.0.0.1:{settings.port}')
        app.custom_brainbox_cache_folder = locations.cache_folder
