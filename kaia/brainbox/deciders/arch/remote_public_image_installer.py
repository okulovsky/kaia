from .docker_installer import DockerInstaller, DockerService
from kaia.brainbox.deployment import RemotePublicImageSource, IContainerRunner


class RemotePublicImageInstaller(DockerInstaller):
    def __init__(self,
                 public_image_address: str,
                 container_name: str,
                 main_service: DockerService
                 ):


        source = RemotePublicImageSource(public_image_address, container_name)

        super().__init__(
            source,
            main_service,
        )


