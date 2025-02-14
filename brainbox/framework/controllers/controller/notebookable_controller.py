from abc import ABC, abstractmethod
from .run_configuration import RunConfiguration
from .docker_controller import DockerController
from typing import cast

class INotebookableController(ABC):
    @abstractmethod
    def get_notebook_configuration(self) -> RunConfiguration:
        pass

    def run_notebook(self):
        self.run_with_configuration(self.get_notebook_configuration())


