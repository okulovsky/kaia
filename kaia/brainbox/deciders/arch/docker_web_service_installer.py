from .docker_installer import DockerInstaller
from abc import ABC, abstractmethod
from kaia.brainbox.deployment import LocalExecutor, IImageSource, IImageBuilder, Deployment, IContainerRunner
from ...core.small_classes import IInstaller, IApiDecider
from .docker_service import DockerService


class DockerWebServiceInstaller(DockerInstaller, ABC):
    def __init__(self,
                 image_source: IImageSource,
                 main_service: DockerService,
                 image_builder: None | IImageBuilder = None
    ):
        self._address = '127.0.0.1'
        super().__init__(image_source, main_service, image_builder)

    def warmup(self, parameters: str):
        self.run_if_not_running_and_wait()

    def cooldown(self, parameters: str):
        self.kill()

    def create_brainbox_decider_api(self, parameters: str) -> IApiDecider:
        return self.create_api()

    def is_running(self) -> bool:
        return self._main_service.is_running()

    @abstractmethod
    def create_api(self):
        pass

    def run_if_not_running_and_wait(self):
        if not self.is_running():
            self.run()
            self.wait_for_running()
        return self.create_api()

    def run_in_any_case_and_create_api(self):
        if not self.is_installed():
            self.install()
        self.run_if_not_running_and_wait()
        return self.create_api()


    @property
    def ip_address(self):
        return self.executor.get_machine().ip_address


    def run(self):
        return self._main_service.run()

    def wait_for_running(self):
        self._main_service.wait_for_running()

    def kill(self):
        return self._main_service.kill()

















