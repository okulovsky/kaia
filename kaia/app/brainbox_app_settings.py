from dataclasses import dataclass
from .app import KaiaApp, IAppInitializer
from brainbox.framework import BrainBoxServer, BrainBoxServiceSettings, ControllerRegistry, Locator, AlwaysOnPlanner, BrainBoxApi
import os
@dataclass
class BrainboxAppSettings(IAppInitializer):
    deciders_files_in_kaia_working_folder: bool = True

    def bind_app(self, app: 'KaiaApp'):
        os.makedirs(app.working_folder / 'brainbox', exist_ok=True)
        registry = ControllerRegistry.discover()
        locator = Locator(app.working_folder / 'brainbox')
        if self.deciders_files_in_kaia_working_folder:
            registry.locator = locator
        settings = BrainBoxServiceSettings(
            registry,
            AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart),
            locator=locator,
            stop_controllers_at_termination=False,
            port=8090,
        )
        app.brainbox_server = BrainBoxServer(settings)
        app.brainbox_api = BrainBoxApi(f'127.0.0.1:{settings.port}')
        app.custom_brainbox_cache_folder = locator.cache_folder
