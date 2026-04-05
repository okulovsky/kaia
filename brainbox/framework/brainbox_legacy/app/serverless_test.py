from typing import *
from ...common import IDecider
from .service import BrainBoxService, BrainBoxServiceSettings
from ...controllers import ControllerRegistry, IController
from ...common import Locator, Loc
from ...job_processing import IPlanner


class ServerlessTest:
    def __init__(self,
                 services: Iterable[Union[IController, IDecider]],
                 allow_failures: bool = False,
                 planner: IPlanner | None = None,
                 ):
        self.services = services
        self.allow_failures = allow_failures
        self.planner = planner
        self.folder = Loc.create_test_folder('brainbox_serverless_test_runs')


    def __enter__(self) -> BrainBoxService:
        self.folder.__enter__()
        locator = Locator(self.folder.path)
        settings = BrainBoxServiceSettings(
            ControllerRegistry(self.services),
            locator=locator,
        )
        if self.planner is not None:
            settings.planner = self.planner
        self._service = BrainBoxService(settings)
        self._service.run()
        return self._service


    def __exit__(self, exc_type, exc_val, exc_tb):
        self._service.shutdown()
        self.folder.__exit__(exc_type, exc_val, exc_tb)




