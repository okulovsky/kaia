from .docker_web_service_installer import DockerWebServiceInstaller
from .docker_service import DockerService
from kaia.brainbox.deployment import RemotePublicImageSource


class RemotePublicImageInstaller(DockerWebServiceInstaller):
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


