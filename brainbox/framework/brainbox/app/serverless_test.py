from typing import *
from ...common import IDecider
from .service import BrainBoxService, BrainBoxServiceSettings
from ...controllers import ControllerRegistry, IController
from ...common import LocHolder, Loc


class ServerlessTest:
    def __init__(self,
                 services: Iterable[Union[Union[IController, IDecider]]],
                 time_limit_in_seconds: int = 10,
                 allow_failures: bool = False,
                 ):
        self.services = services
        self.time_limit_in_seconds = time_limit_in_seconds
        self.allow_failures = allow_failures
        self.folder = Loc.create_test_folder('brainbox_serverless_test_runs')


    def __enter__(self) -> BrainBoxService:
        self.folder.__enter__()
        locator = LocHolder(self.folder.path)
        self._service = BrainBoxService(BrainBoxServiceSettings(
            ControllerRegistry(self.services),
            locator=locator
        ))
        self._service.run()
        return self._service


    def __exit__(self, exc_type, exc_val, exc_tb):
        self._service.shutdown()
        self.folder.__exit__(exc_type, exc_val, exc_tb)




