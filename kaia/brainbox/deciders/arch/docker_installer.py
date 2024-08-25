import shutil
from kaia.brainbox.deployment import LocalExecutor, IImageSource, IImageBuilder, Deployment, IContainerRunner
from ...core.small_classes import IInstaller
from .docker_service import DockerService
from uuid import uuid4



class DockerInstaller(IInstaller):
    def __init__(self,
                 image_source: IImageSource,
                 main_service: DockerService,
                 image_builder: None | IImageBuilder = None
    ):
        self._executor = LocalExecutor()
        self._address = '127.0.0.1'
        self._image_builder = image_builder
        self._image_source = image_source
        self._main_service = main_service

    @property
    def name(self):
        return self._image_source.get_container_name()

    @property
    def executor(self):
        return self._executor

    def is_installed(self):
        return len(self._image_source.get_relevant_images(self._executor)) > 0

    def install(self):
        self.pre_install()
        self._main_service.get_deployment().stop().remove().obtain_image()
        self.post_install()

    def pre_install(self):
        pass

    def post_install(self):
        pass

    def resource_folder(self, *subfolders):
        folder = self._executor.get_machine().data_folder/'deciders_resources'/self.name
        for subfolder in subfolders:
            if subfolder is not None:
                folder /= subfolder
        self._executor.create_empty_folder(folder)
        return folder

    @property
    def ip_address(self):
        return self._executor.get_machine().ip_address

    def uninstall(self, purge: bool = False):
        self.main_service.get_deployment().stop().remove()
        images = self._image_source.get_relevant_images(self._executor)
        for image in images:
            self._executor.execute(['docker', 'rmi', image])
        if purge:
            shutil.rmtree(self.resource_folder())

    def is_running(self) -> bool:
        return self._main_service.is_running()

    def run(self):
        return self._main_service.run()

    def wait_for_running(self):
        self._main_service.wait_for_running()

    def kill(self):
        return self._main_service.kill()

    @property
    def main_service(self) -> DockerService:
        return self._main_service















