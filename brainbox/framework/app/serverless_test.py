from threading import Thread
from brainbox.framework.common import BrainBoxLocations
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.job_processing import SimplePlanner, IPlanner
from .api import BrainBoxApi
from .server import BrainBoxServer, BrainBoxServerSettings, BrainBoxServices
from foundation_kaia.misc import Loc


class ServerlessTest:
    def __init__(self,
                 settings: BrainBoxServerSettings | None = None,
                 registry: ControllerRegistry | None = None,
                 planner: IPlanner | None = None,
                 ):
        self._provided_settings = settings
        self._registry = registry
        self._planner = planner
        self._services: BrainBoxServices | None = None
        self._loop_thread: Thread | None = None
        self._temp_folder = None

    def __enter__(self) -> BrainBoxApi:
        if self._provided_settings is not None:
            settings = self._provided_settings
        else:
            self._temp_folder = Loc.create_test_folder('serverless_test')
            self._temp_folder.__enter__()
            settings = BrainBoxServerSettings(
                registry=self._registry or ControllerRegistry([]),
                planner=self._planner or SimplePlanner(),
                locations=BrainBoxLocations.default(self._temp_folder.path)
            )

        self._services = BrainBoxServer.create_services(settings)
        self._loop_thread = Thread(target=self._services.loop.run, daemon=True)
        self._loop_thread.start()

        api = object.__new__(BrainBoxApi)
        api.tasks = self._services.tasks
        api.controllers = self._services.controllers
        api.batches = self._services.batches
        api.cache = self._services.cache
        api.streaming_cache = self._services.streaming_cache
        api.resources = self._services.resources
        api.debug_locations = settings.locations
        api.debug_resources_folder = settings.registry.resources_folder
        api.diagnostics = self._services.diagnostics
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._services is not None:
            self._services.loop.terminate()
        if self._loop_thread is not None:
            self._loop_thread.join(timeout=5)
        if self._temp_folder is not None:
            self._temp_folder.__exit__(exc_type, exc_val, exc_tb)
